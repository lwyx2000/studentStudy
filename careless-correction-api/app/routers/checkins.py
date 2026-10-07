from datetime import datetime, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import CheckIn, HabitSOP, PendingSunlight, SOPStep, SubTask, SunlightHistory, Task, User
from app.routers.badges import auto_unlock_badges
from app.schemas import TaskOut

router = APIRouter()


def _parse_check_date(check_date: str):
    """解析打卡日期字符串（支持 2026/8/1、2026-08-01），失败返回 None。"""
    try:
        if '/' in check_date:
            y, m, d = check_date.split('/')
        elif '-' in check_date:
            y, m, d = check_date.split('-')
        else:
            return None
        return datetime(int(y), int(m), int(d)).date()
    except Exception:
        return None


def _normalize_check_date(raw: str) -> str | None:
    """归一化打卡日期为 YYYY-MM-DD，保证同一日期不因格式差异（2026/9/1 vs 2026-09-01）分裂成多条记录。"""
    d = _parse_check_date(raw)
    return d.isoformat() if d else None


def _update_streak_days(child: User, db: Session, check_date: str):
    """根据打卡日期更新连续打卡天数（计入本次通过的打卡）。

    直接用 SQL 拉取该孩子所有已通过打卡的去重日期，避免 limit 截断导致长期使用后 streak 不准。
    """
    current = _parse_check_date(check_date) or datetime.now().date()

    date_strs = (
        db.query(CheckIn.check_date)
        .filter(
            CheckIn.fk_users == child.pk_users,
            CheckIn.status == 'approved',
        )
        .distinct()
        .all()
    )
    dates = {_parse_check_date(s[0]) for s in date_strs}
    dates.discard(None)
    # 显式把本次打卡日期加入集合，避免依赖 autoflush 行为
    dates.add(current)

    # 从 current 向前数连续天数
    streak = 0
    cursor = current
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    child.streak_days = streak


def _sanitize_completed_tasks_snapshot(raw: str | None) -> str | None:
    """清洗前端传来的完成项快照 JSON：只保留 title/icon/points，限制数量与长度。"""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return None
        cleaned = []
        for item in data[:100]:
            if not isinstance(item, dict):
                continue
            title = str(item.get('title', ''))[:100]
            if not title:
                continue
            cleaned.append({
                'title': title,
                'icon': str(item.get('icon', ''))[:10],
                'points': max(0, min(9999, int(item.get('points', 0) or 0))),
            })
        return json.dumps(cleaned, ensure_ascii=False) if cleaned else None
    except Exception:
        return None


def _load_snapshot(snapshot_json: str | None) -> list[dict]:
    if not snapshot_json:
        return []
    try:
        data = json.loads(snapshot_json)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _checkin_to_dict(r: CheckIn, child: User | None = None) -> dict:
    child_name = child.name if child else None
    snapshot = _load_snapshot(r.completed_tasks_snapshot)
    return {
        'id': r.pk_check_ins,
        'childId': r.fk_users,
        'childName': child_name,
        'checkDate': r.check_date,
        'totalPoints': r.total_points,
        'habitStepCount': r.habit_step_count,
        # 有快照时完成任务数以快照条目数为准，与详情列表保持一致
        # （旧记录 task_count 存的是主任务数，与小任务明细列表对不上）
        'taskCount': len(snapshot) if snapshot else r.task_count,
        'requiredPoints': r.required_points,
        'optionalBonus': r.optional_bonus,
        'allDoneBonus': r.all_done_bonus,
        'habitPoints': r.habit_points,
        'rejectReason': r.reject_reason,
        'status': r.status,
        'createdAt': r.created_at.isoformat() if r.created_at else None,
        'approvedAt': r.approved_at.isoformat() if r.approved_at else None,
        'completedTasksSnapshot': snapshot,
    }


@router.post('/')
def submit_checkin(
    check_date: str,
    total_points: int = 0,
    habit_step_count: int = 0,
    task_count: int = 0,
    required_points: int = 0,
    optional_bonus: int = 0,
    all_done_bonus: int = 0,
    habit_points: int = 0,
    completed_tasks: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized = _normalize_check_date(check_date)
    if not normalized:
        raise HTTPException(status_code=400, detail='打卡日期格式无效')

    # 服务端兜底校验：积分不可为负，总分不得超过该孩子当日理论可得上限
    # （前端计算正确时永远不会触发，仅防御改包/伪造请求刷阳光）
    total_points = max(0, total_points)
    task_sum = sum(
        t.reward_points for t in
        db.query(Task).filter(Task.fk_users == current_user.pk_users, Task.active == True).all()
    )
    # 子任务可单独设分值（可能高于主任务默认分），上限需加上全部子任务的分值总和
    subtask_sum = sum(
        (s.reward_points or 0) for s in
        db.query(SubTask)
        .join(Task, SubTask.fk_tasks == Task.pk_tasks)
        .filter(Task.fk_users == current_user.pk_users, Task.active == True).all()
    )
    # 习惯计分与前端口径一致：每勾选一步 = 该习惯完整分值（分值 × 步骤数）
    habit_sum = sum(
        (h.reward_points or 0) * len(h.steps)
        for h in db.query(HabitSOP).options(selectinload(HabitSOP.steps))
              .filter(HabitSOP.fk_users == current_user.pk_users, HabitSOP.active == True).all()
    )
    # +10 全完成奖励；可选⭐每项 +2，缓冲按 100 分覆盖极端配置
    max_possible = max(task_sum, subtask_sum) + habit_sum + 110
    if total_points > max_possible:
        total_points = max_possible
    # 分项同理夹取，保证明细之和不超过总分（审批弹层展示用）
    required_points = max(0, min(required_points, total_points))
    habit_points = max(0, min(habit_points, total_points))
    optional_bonus = max(0, min(optional_bonus, 100))
    all_done_bonus = max(0, min(all_done_bonus, 10))

    snapshot = _sanitize_completed_tasks_snapshot(completed_tasks)

    # 支持同日多次提交：如果当天已有未审批通过的打卡，用新提交覆盖旧记录（保留 id 与 created_at，仅更新积分与快照）
    # 已通过(approved)的记录不允许重复提交，避免同一天重复获得阳光
    existing = db.query(CheckIn).filter(
        CheckIn.fk_users == current_user.pk_users,
        CheckIn.check_date == normalized,
        CheckIn.status.in_(['pending', 'rejected']),
    ).order_by(CheckIn.pk_check_ins.desc()).first()
    if existing:
        if existing.status == 'rejected':
            existing.status = 'pending'
            existing.reject_reason = None
        # 用新提交覆盖旧积分（不累加）
        existing.total_points = total_points
        existing.habit_step_count = habit_step_count
        existing.task_count = task_count
        existing.required_points = required_points
        existing.optional_bonus = optional_bonus
        existing.all_done_bonus = all_done_bonus
        existing.habit_points = habit_points
        existing.completed_tasks_snapshot = snapshot
        existing.approved_at = None
        db.commit()
        db.refresh(existing)
        return {'checkin': existing, 'updated': True}

    # 若同日已有已通过(approved)的打卡，不允许重复提交，避免重复获得阳光
    already_approved = db.query(CheckIn).filter(
        CheckIn.fk_users == current_user.pk_users,
        CheckIn.check_date == normalized,
        CheckIn.status == 'approved',
    ).first()
    if already_approved:
        raise HTTPException(status_code=400, detail='该日期打卡已审批通过，无需重复提交')

    record = CheckIn(
        fk_users=current_user.pk_users,
        check_date=normalized,
        total_points=total_points,
        habit_step_count=habit_step_count,
        task_count=task_count,
        required_points=required_points,
        optional_bonus=optional_bonus,
        all_done_bonus=all_done_bonus,
        habit_points=habit_points,
        completed_tasks_snapshot=snapshot,
        status='pending',
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'checkin': record, 'updated': False}


@router.get('/mine')
def list_my_checkins(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """孩子查看自己的打卡记录（含审批状态与驳回原因）。"""
    limit = max(1, min(limit, 200))
    records = (
        db.query(CheckIn)
        .filter(CheckIn.fk_users == current_user.pk_users)
        .order_by(CheckIn.pk_check_ins.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(CheckIn).filter(CheckIn.fk_users == current_user.pk_users).count()
    return {'checkins': [_checkin_to_dict(r) for r in records], 'total': total, 'offset': offset, 'limit': limit}


@router.get('/pending')
def list_pending_checkins(
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    records = (
        db.query(CheckIn)
        .join(User, CheckIn.fk_users == User.pk_users)
        .filter(
            User.fk_users_parent == current_user.pk_users,
            CheckIn.status == 'pending',
        )
        .order_by(CheckIn.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = (
        db.query(CheckIn)
        .join(User, CheckIn.fk_users == User.pk_users)
        .filter(
            User.fk_users_parent == current_user.pk_users,
            CheckIn.status == 'pending',
        )
        .count()
    )
    result = []
    for r in records:
        child = db.query(User).filter(User.pk_users == r.fk_users).first()
        result.append(_checkin_to_dict(r, child))
    return {'pending': result, 'total': total, 'offset': offset, 'limit': limit}


@router.post('/{checkin_id}/approve')
def approve_checkin(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(CheckIn).filter(CheckIn.pk_check_ins == checkin_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='打卡记录不存在')
    child = db.query(User).filter(User.pk_users == record.fk_users).first()
    if not child or child.fk_users_parent != current_user.pk_users:
        raise HTTPException(status_code=403, detail='无权审批该打卡')
    if record.status not in ('pending', 'rejected'):
        raise HTTPException(status_code=400, detail='该打卡已审批')
    record.status = 'approved'
    record.approved_at = datetime.now()
    record.reject_reason = None
    # 不再直接增加 sunlight_points，而是生成「待收集阳光」记录
    # 孩子需在阳光树页面点击收集后才正式变为阳光值
    if record.total_points > 0:
        # 重复审批（驳回后重新通过）时避免重复生成待收集阳光
        already_pending = (
            db.query(PendingSunlight)
            .filter(
                PendingSunlight.fk_check_ins == record.pk_check_ins,
                PendingSunlight.collected == False,
            )
            .first()
        )
        if not already_pending:
            pending = PendingSunlight(
                fk_users=child.pk_users,
                amount=record.total_points,
                reason=f'打卡审批通过（{record.check_date}）',
                fk_check_ins=record.pk_check_ins,
                collected=False,
            )
            db.add(pending)
    # 更新连续打卡天数
    _update_streak_days(child, db, record.check_date)
    db.commit()
    # Auto-unlock badges after checkin approval
    newly_unlocked = auto_unlock_badges(child, db)
    return {
        'success': True,
        'childName': child.name,
        'awarded': record.total_points,
        'pendingSunlight': True,
        'balance': child.sunlight_points,
        'streakDays': child.streak_days,
        'newly_unlocked_badges': newly_unlocked,
    }


@router.post('/{checkin_id}/reject')
def reject_checkin(
    checkin_id: int,
    reason: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(CheckIn).filter(CheckIn.pk_check_ins == checkin_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='打卡记录不存在')
    child = db.query(User).filter(User.pk_users == record.fk_users).first()
    if not child or child.fk_users_parent != current_user.pk_users:
        raise HTTPException(status_code=403, detail='无权审批该打卡')
    if record.status != 'pending':
        raise HTTPException(status_code=400, detail='该打卡已审批')
    record.status = 'rejected'
    record.reject_reason = (reason or '').strip()[:500] or None
    db.commit()
    return {'success': True, 'childName': child.name}


@router.post('/{checkin_id}/reopen')
def reopen_checkin(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """误驳回后重新打开为待审批状态。"""
    record = db.query(CheckIn).filter(CheckIn.pk_check_ins == checkin_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='打卡记录不存在')
    child = db.query(User).filter(User.pk_users == record.fk_users).first()
    if not child or child.fk_users_parent != current_user.pk_users:
        raise HTTPException(status_code=403, detail='无权操作该打卡')
    if record.status != 'rejected':
        raise HTTPException(status_code=400, detail='仅已驳回的打卡可重新审批')
    record.status = 'pending'
    record.reject_reason = None
    db.commit()
    return {'success': True, 'childName': child.name}


@router.get('/history')
def get_checkin_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取已审批的打卡历史记录"""
    limit = max(1, min(limit, 200))
    query = (
        db.query(CheckIn)
        .join(User, CheckIn.fk_users == User.pk_users)
        .filter(
            User.fk_users_parent == current_user.pk_users,
            CheckIn.status != 'pending',
        )
    )
    total = query.count()
    records = query.order_by(CheckIn.pk_check_ins.desc()).offset(offset).limit(limit).all()
    result = []
    for r in records:
        child = db.query(User).filter(User.pk_users == r.fk_users).first()
        result.append(_checkin_to_dict(r, child))
    return {'history': result, 'total': total, 'offset': offset, 'limit': limit}


@router.get('/{checkin_id}/details')
def get_checkin_details(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取打卡详情，包括孩子的任务完成情况和习惯数据"""
    record = db.query(CheckIn).filter(CheckIn.pk_check_ins == checkin_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='打卡记录不存在')
    child = db.query(User).filter(User.pk_users == record.fk_users).first()
    if not child or child.fk_users_parent != current_user.pk_users:
        raise HTTPException(status_code=403, detail='无权查看该打卡')

    # 提交时保存的完成项快照：任务每日重置后详情依然可回看当日完成情况
    snapshot_tasks = _load_snapshot(record.completed_tasks_snapshot)

    # 获取孩子的所有任务（含子任务）
    tasks = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(Task.fk_users == child.pk_users, Task.active == True)
        .order_by(Task.type)
        .all()
    )

    # 获取孩子的所有活跃习惯（含步骤）
    habits = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.fk_users == child.pk_users, HabitSOP.active == True)
        .order_by(HabitSOP.created_at.desc())
        .all()
    )

    # 解析打卡日期
    check_date = _parse_check_date(record.check_date)

    # 统计已完成任务（有快照时以快照为准，避免每日重置后失真）
    completed_tasks: list[dict] = []
    pending_tasks: list[dict] = []
    if snapshot_tasks:
        completed_tasks = [
            {
                'pk_tasks': f'snap-{i}',
                'title': item.get('title', ''),
                'description': '',
                'icon': item.get('icon') or '📋',
                'reward_points': item.get('points', 0),
                'sub_tasks': [],
                'from_snapshot': True,
            }
            for i, item in enumerate(snapshot_tasks)
        ]
        pending_tasks = [TaskOut.model_validate(t).model_dump(mode='json') for t in tasks if t.status != 'completed']
    else:
        for t in tasks:
            task_dict = TaskOut.model_validate(t).model_dump(mode='json')
            if t.status == 'completed':
                # 如果有完成时间且与打卡日期匹配，优先显示
                if t.completed_at and check_date:
                    if t.completed_at.date() == check_date:
                        completed_tasks.append(task_dict)
                    else:
                        pending_tasks.append(task_dict)
                else:
                    completed_tasks.append(task_dict)
            else:
                pending_tasks.append(task_dict)

    habit_list = []
    for h in habits:
        habit_dict = {
            'pk_habit_sops': h.pk_habit_sops,
            'title': h.title,
            'reward_points': h.reward_points,
            'steps': [
                {
                    'order': s.order,
                    'instruction': s.instruction,
                    'image_url': s.image_url,
                    'gif_url': s.gif_url,
                }
                for s in h.steps
            ],
        }
        habit_list.append(habit_dict)

    return {
        'checkin': {
            'id': record.pk_check_ins,
            'childName': child.name,
            'checkDate': record.check_date,
            'totalPoints': record.total_points,
            'habitStepCount': record.habit_step_count,
            # 完成任务数与下方 completedTasks 列表条数保持一致：
            # 有快照时取快照条目数（旧记录 task_count 为主任务数，与列表对不上）
            'taskCount': len(completed_tasks) if snapshot_tasks else record.task_count,
            'requiredPoints': record.required_points,
            'optionalBonus': record.optional_bonus,
            'allDoneBonus': record.all_done_bonus,
            'habitPoints': record.habit_points,
            'rejectReason': record.reject_reason,
            'status': record.status,
            'createdAt': record.created_at.isoformat() if record.created_at else None,
            'streakDays': child.streak_days,
        },
        'completedTasks': completed_tasks,
        'pendingTasks': pending_tasks,
        'habits': habit_list,
    }
