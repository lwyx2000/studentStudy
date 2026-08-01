import asyncio
import math
import uuid
from datetime import date, datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import SubTask, Task, User
from app.schemas import SubTaskOut, TaskOut

# ── In-memory scan batch store ──
scan_batches: dict[str, dict] = {}

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


@router.post('/checkin')
async def checkin(
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f'task_{current_user.pk_users}_{datetime.now().timestamp()}_{photo.filename}'
    content = await photo.read()
    file_path.write_bytes(content)
    photo_url = f'/uploads/{file_path.name}'
    return {'photoUrl': photo_url, 'recognized': True}


def _detect_checked_boxes(image_path: str) -> list[dict]:
    """Use OpenCV to detect filled checkboxes in a scanned checklist photo.
    
    Returns list of detected box regions with checked status.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Lighting normalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Adaptive threshold to binary
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 3)

    # Remove long lines (table borders) to isolate checkboxes
    horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                                   cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 30, 3), 1)))
    vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                                 cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 30, 3))))
    lines = cv2.bitwise_or(horizontal, vertical)
    clean = cv2.bitwise_xor(thresh, lines)

    # Find contours
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_box = max(w * 0.008, 8)
    max_box = max(w * 0.06, 60)
    results = []

    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw < min_box or bh < min_box or bw > max_box or bh > max_box:
            continue
        aspect = bw / max(bh, 1)
        if aspect < 0.4 or aspect > 2.5:
            continue

        # Calculate fill ratio inside bounding rect
        roi = thresh[y:y + bh, x:x + bw]
        fill = cv2.countNonZero(roi) / (bw * bh)

        results.append({
            'x': int(x), 'y': int(y), 'w': int(bw), 'h': int(bh),
            'fill': round(fill, 3),
            'checked': fill > 0.25,
        })

    return results


@router.post('/scan')
async def scan_checklist(
    photo: UploadFile = File(...),
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a photo of the printed checklist; detect checked boxes via OpenCV."""
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f'scan_{current_user.pk_users}_{datetime.now().timestamp()}_{photo.filename}'
    content = await photo.read()
    file_path.write_bytes(content)
    photo_url = f'/uploads/{file_path.name}'

    boxes = _detect_checked_boxes(str(file_path))
    checked_count = sum(1 for b in boxes if b['checked'])

    target = resolve_target_user(current_user, child_id, db)
    today_tasks = (
        db.query(Task)
        .filter(
            Task.fk_users == target.pk_users,
            Task.assigned_date == date.today(),
            Task.active == True,
        )
        .order_by(Task.type)
        .all()
    )

    # If we detected exactly the right number of boxes, mark tasks in order
    completed_ids: list[int] = []
    if checked_count > 0 and len(today_tasks) > 0:
        checked_ids = [t.pk_tasks for t in today_tasks[:checked_count]
                       if t.status == 'pending']
        for task_id in checked_ids:
            task = db.query(Task).filter(Task.pk_tasks == task_id).first()
            if task and task.status == 'pending':
                task.status = 'completed'
                task.completed_at = datetime.now()
                # 阳光值不再在此处自动发放，统一由家长审批打卡 (checkins/approve) 后发放
                task.completion_photo_url = photo_url
                completed_ids.append(task_id)
        db.commit()

    return {
        'photoUrl': photo_url,
        'checkedCount': checked_count,
        'detectedBoxes': len(boxes),
        'tasksCompleted': completed_ids,
    }


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


async def _process_scan_batch(batch_id: str):
    """Background worker that processes each file in the batch."""
    batch = scan_batches.get(batch_id)
    if not batch:
        return
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    photo_urls: list[str] = []
    for i, file_bytes in enumerate(batch['pending_files']):
        filename = batch['filenames'][i]
        file_path = upload_dir / f'scan_{batch_id}_{i}_{filename}'
        file_path.write_bytes(file_bytes)
        photo_url = f'/uploads/{file_path.name}'
        photo_urls.append(photo_url)

        try:
            boxes = _detect_checked_boxes(str(file_path))
            checked_count = sum(1 for b in boxes if b['checked'])
            batch['results'].append({
                'filename': filename,
                'photoUrl': photo_url,
                'checkedCount': checked_count,
                'detectedBoxes': len(boxes),
            })
            batch['completed'] += 1
        except Exception:
            batch['failed'] += 1
            batch['errors'].append(filename)
        batch['progress'] = batch['completed'] + batch['failed']
        await asyncio.sleep(0.05)  # yield control
    # Mark done and update task completion counts
    batch['done'] = True
    batch.pop('pending_files', None)
    batch.pop('filenames', None)


@router.post('/scan/batch')
async def scan_batch(
    photos: list[UploadFile] = File(...),
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
):
    """Upload multiple checklist photos; process asynchronously.
    Returns a batch_id to poll for status.
    """
    batch_id = uuid.uuid4().hex[:12]
    pending_files: list[bytes] = []
    filenames: list[str] = []
    for photo in photos:
        content = await photo.read()
        pending_files.append(content)
        filenames.append(photo.filename or 'photo.jpg')

    scan_batches[batch_id] = {
        'total': len(pending_files),
        'progress': 0,
        'completed': 0,
        'failed': 0,
        'done': False,
        'results': [],
        'errors': [],
        'pending_files': pending_files,
        'filenames': filenames,
    }
    asyncio.create_task(_process_scan_batch(batch_id))
    return {'batchId': batch_id, 'total': len(pending_files)}


@router.get('/scan/batch/{batch_id}')
def get_scan_batch_status(batch_id: str):
    """Poll scan batch progress."""
    batch = scan_batches.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail='批次不存在')
    return {
        'total': batch['total'],
        'progress': batch['progress'],
        'completed': batch['completed'],
        'failed': batch['failed'],
        'done': batch['done'],
        'results': batch['results'],
        'errors': batch['errors'],
    }
