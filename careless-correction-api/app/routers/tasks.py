from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Task, User
from app.schemas import TaskOut

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


@router.get('/today')
def get_today_tasks(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target_user(current_user, child_id, db)
    tasks = (
        db.query(Task)
        .filter(Task.fk_users == target.pk_users, Task.assigned_date == date.today())
        .order_by(Task.type)
        .all()
    )
    return {'tasks': [TaskOut.model_validate(t) for t in tasks]}


@router.post('/{task_id}/complete')
def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(
        Task.pk_tasks == task_id,
        Task.fk_users == current_user.pk_users,
        Task.status == 'pending',
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在或已完成')
    task.status = 'completed'
    task.completed_at = datetime.now()
    current_user.sunlight_points += task.reward_points
    db.commit()
    db.refresh(task)
    return {'task': TaskOut.model_validate(task), 'pointsEarned': task.reward_points}


@router.post('/checkin')
async def checkin(
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    from pathlib import Path
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f'task_{current_user.pk_users}_{datetime.now().timestamp()}_{photo.filename}'
    content = await photo.read()
    file_path.write_bytes(content)
    photo_url = f'/uploads/{file_path.name}'
    return {'photoUrl': photo_url, 'recognized': True}


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
        assigned_date=date.today(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {'task': TaskOut.model_validate(task)}


@router.delete('/{task_id}')
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.pk_tasks == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    # 只有任务所有者或其家长可删除
    if task.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == task.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    db.delete(task)
    db.commit()
    return {'success': True}
