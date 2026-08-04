import asyncio
import math
import uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import SubTask, Task, User
from app.schemas import SubTaskOut, TaskOut


router = APIRouter()


def resolve_target_user(current_user: User, child_id: int | None, db: Session) -> User:
    """家长可通过 child_id 操作孩子数据，否则操作自己的数据"""
    if child_id is None:
        return current_user
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='无权访问')
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    return child


def _reset_daily_tasks(target_user: User, db: Session):
    """将昨天及之前已完成且仍 active 的任务重置为 pending，assigned_date 更新为今天。
    这样每日重复任务每天都会出现在孩子的待办列表中。
    """
    today = date.today()
    stale_tasks = (
        db.query(Task)
        .filter(
            Task.fk_users == target_user.pk_users,
            Task.assigned_date < today,
            Task.status == 'completed',
            Task.active == True,
        )
        .all()
    )
    for task in stale_tasks:
        task.status = 'pending'
        task.assigned_date = today
        task.completed_at = None
        task.completion_photo_url = None
    if stale_tasks:
        db.commit()


@router.get('/today')
def get_today_tasks(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target_user(current_user, child_id, db)
    # 自动重置每日任务
    _reset_daily_tasks(target, db)
    tasks = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(
            Task.fk_users == target.pk_users,
            Task.status == 'pending',
            Task.active == True,
        )
        .order_by(Task.type)
        .all()
    )
    return {'tasks': [TaskOut.model_validate(t) for t in tasks]}


@router.get('/inventory')
def get_task_inventory(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有任务（包括 inactive 的），用于任务清单页面"""
    target = resolve_target_user(current_user, child_id, db)
    tasks = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(Task.fk_users == target.pk_users)
        .order_by(Task.active.desc(), Task.assigned_date.desc())
        .all()
    )
    return {'tasks': [TaskOut.model_validate(t) for t in tasks]}


@router.get('/{task_id}', response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(Task.pk_tasks == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    return task


@router.post('/{task_id}/complete')
def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(
            Task.pk_tasks == task_id,
            Task.fk_users == current_user.pk_users,
            Task.status == 'pending',
            Task.active == True,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在或已完成')
    task.status = 'completed'
    task.completed_at = datetime.now()
    # 阳光值不再在此处自动发放，统一由家长审批打卡 (checkins/approve) 后发放
    db.commit()
    db.refresh(task)
    return {'task': TaskOut.model_validate(task), 'pointsEarned': task.reward_points}


@router.get('/checkin/history')
def get_checkin_history(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target_user(current_user, child_id, db)
    tasks = (
        db.query(Task)
        .filter(Task.fk_users == target.pk_users, Task.completion_photo_url.isnot(None))
        .order_by(Task.completed_at.desc())
        .limit(50)
        .all()
    )
    return {
        'history': [
            {'id': t.pk_tasks, 'title': t.title, 'completionPhotoUrl': t.completion_photo_url,
             'completedAt': t.completed_at.isoformat() if t.completed_at else None}
            for t in tasks
        ],
    }


@router.post('/', status_code=201)
def create_task(
    title: str,
    type: str,
    description: str | None = None,
    reward_points: int = 10,
    icon: str | None = None,
    week_day: str | None = None,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家长创建任务（指定孩子）"""
    target = resolve_target_user(current_user, child_id, db)
    task = Task(
        fk_users=target.pk_users,
        title=title,
        description=description,
        type=type,
        reward_points=reward_points,
        icon=icon,
        week_day=week_day,
        assigned_date=date.today(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {'task': TaskOut.model_validate(task)}


@router.put('/{task_id}')
def update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    type: str | None = None,
    reward_points: int | None = None,
    icon: str | None = None,
    week_day: str | None = None,
    active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).options(selectinload(Task.sub_tasks)).filter(Task.pk_tasks == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if type is not None:
        task.type = type
    if reward_points is not None:
        task.reward_points = reward_points
    if icon is not None:
        task.icon = icon
    if week_day is not None:
        task.week_day = week_day
    if active is not None:
        task.active = active
    db.commit()
    db.refresh(task)
    return {'task': TaskOut.model_validate(task)}


@router.delete('/{task_id}')
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """软删除：将任务标记为 inactive（不在管理页面显示，但保留在清单中）"""
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    # 只有任务所有者或其家长可操作
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    task.active = False
    db.commit()
    return {'success': True, 'softDelete': True}


@router.delete('/{task_id}/permanent')
def delete_task_permanent(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """永久删除任务（仅从任务清单页面调用）"""
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    db.delete(task)
    db.commit()
    return {'success': True}


@router.get('/subtasks/library')
def get_subtask_library(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有子任务库（用于复用）"""
    target = resolve_target_user(current_user, child_id, db)
    subtasks = (
        db.query(SubTask)
        .join(Task, SubTask.fk_tasks == Task.pk_tasks)
        .filter(Task.fk_users == target.pk_users)
        .order_by(SubTask.created_at.desc())
        .all()
    )
    return {'subtasks': [
        {
            'pk_sub_tasks': s.pk_sub_tasks,
            'title': s.title,
            'type': s.type,
            'week_day': s.week_day,
            'sort_order': s.sort_order,
            'created_at': s.created_at,
            'task_title': db.query(Task.title).filter(Task.pk_tasks == s.fk_tasks).scalar(),
        }
        for s in subtasks
    ]}


@router.post('/{task_id}/subtasks', response_model=SubTaskOut, status_code=201)
def add_subtask(
    task_id: int,
    title: str,
    type: str | None = None,
    week_day: str | None = None,
    sort_order: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """给任务添加子任务（type 默认继承主任务类别，week_day: weekday/weekend 区分平时和周末）"""
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    subtask = SubTask(
        fk_tasks=task_id,
        title=title,
        type=type or task.type,
        week_day=week_day,
        sort_order=sort_order,
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.put('/{task_id}/subtasks/{subtask_id}', response_model=SubTaskOut)
def update_subtask(
    task_id: int,
    subtask_id: int,
    title: str | None = None,
    type: str | None = None,
    week_day: str | None = None,
    sort_order: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新子任务"""
    subtask = db.query(SubTask).filter(
        SubTask.pk_sub_tasks == subtask_id,
        SubTask.fk_tasks == task_id,
    ).first()
    if not subtask:
        raise HTTPException(status_code=404, detail='子任务不存在')
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    if title is not None:
        subtask.title = title
    if type is not None:
        subtask.type = type
    if week_day is not None:
        subtask.week_day = week_day
    if sort_order is not None:
        subtask.sort_order = sort_order
    db.commit()
    db.refresh(subtask)
    return subtask


@router.delete('/{task_id}/subtasks/{subtask_id}')
def delete_subtask(
    task_id: int,
    subtask_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除子任务"""
    subtask = db.query(SubTask).filter(
        SubTask.pk_sub_tasks == subtask_id,
        SubTask.fk_tasks == task_id,
    ).first()
    if not subtask:
        raise HTTPException(status_code=404, detail='子任务不存在')
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    db.delete(subtask)
    db.commit()
    return {'success': True}

