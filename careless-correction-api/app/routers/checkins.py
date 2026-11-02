from datetime import date, datetime, timedelta
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


def _approved_dates(child_id: int, db: Session) -> set[date]:
    """该孩子所有已通过审批的打卡日期（去重，已归一化）。"""
    rows = (
        db.query(CheckIn.check_date)
        .filter(CheckIn.fk_users == child_id, CheckIn.status == 'approved')
        .distinct()
        .all()
    )
    dates: set[date] = set()
    for (raw,) in rows:
        d = _parse_check_date(raw)
        if d:
            dates.add(d)
    return dates


def _calc_streak(dates: set[date], anchor: date) -> int:
    """从 anchor 往前数连续天数。

    若 anchor 当天还没有已通过打卡，则从 anchor-1 开始数（今天尚未打卡不清零连击，
    与常见打卡产品一致）。
    """
    cursor = anchor
    if cursor not in dates:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _calc_best_streak(dates: set[date]) -> int:
    """历史最长连续打卡天数。"""
    if not dates:
        return 0
    best = cur = 1
    prev: date | None = None
    for d in sorted(dates):
        if prev is None:
            cur = 1
        elif (d - prev).days == 1:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
        prev = d
    return best


def _has_checked_today(child_id: int, db: Session) -> bool:
    """今天是否已经提交过打卡（待审批也算，已驳回不算）。"""
    today = datetime.now().date()
    rows = (
        db.query(CheckIn.check_date)
        .filter(
            CheckIn.fk_users == child_id,
            CheckIn.status.in_(['pending', 'approved']),
        )
        .all()
    )
    return any(_parse_check_date(raw) == today for (raw,) in rows)


def _streak_snapshot(child: User, db: Session, include_today_pending: bool = True):
    """返回 (当前连续天数, 历史最佳连续天数, 含今日待审批的展示天数)。

    streak_days 以「今天/昨天」为锚点动态计算，因此补打卡历史日期不会把已有连击覆盖掉。
    """
    approved = _approved_dates(child.pk_users, db)
    today = datetime.now().date()
    base = _calc_streak(approved, today)
    display = base
    if include_today_pending and today not in approved and _has_checked_today(child.pk_users, db):
        display = base + 1
    best = max(_calc_best_streak(approved), display)
    return base, best, display


def _refresh_streak_days(child: User, db: Session) -> int:
    """刷新并回写连续打卡天数（仅统计已通过审批的记录）。"""
    base, _best, _display = _streak_snapshot(child, db, include_today_pending=False)
    child.streak_days = base
    return base


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
    # 不允许给未来日期打卡（避免提前刷阳光、污染连续天数统计）
    if _parse_check_date(normalized) > datetime.now().date():
        raise HTTPException(status_code=400, detail='不能给未来日期打卡')

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
    same_date = (
        db.query(CheckIn)
        .filter(CheckIn.fk_users == current_user.pk_users, CheckIn.check_date == normalized)
        .order_by(CheckIn.pk_check_ins.desc())
        .all()
    )
    if any(r.status == 'approved' for r in same_date):
        raise HTTPException(status_code=400, detail='该日期打卡已审批通过，无需重复提交')

    existing = next((r for r in same_date if r.status in ('pending', 'rejected')), None)
    # 清理同日重复待审批记录（并发双击 / 旧数据），否则家长会审批两条、重复发放阳光
    for dup in same_date:
        if existing is not None and dup.pk_check_ins == existing.pk_check_ins:
            continue
        if dup.status in ('pending', 'rejected') and not dup.pending_sunlight_records:
            db.delete(dup)

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
        base, best, display = _streak_snapshot(current_user, db)
        return {
            'checkin': existing,
            'updated': True,
            'streak': {
                'days': display,
                'approvedDays': base,
                'bestDays': best,
                'checkedToday': _has_checked_today(current_user.pk_users, db),
                'isNewToday': False,
                'todayDate': normalized,
            },
        }

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
    base, best, display = _streak_snapshot(current_user, db)
    return {
        'checkin': record,
        'updated': False,
        'streak': {
            'days': display,
            'approvedDays': base,
            'bestDays': best,
            'checkedToday': _has_checked_today(current_user.pk_users, db),
            'isNewToday': _parse_check_date(normalized) == datetime.now().date(),
            'todayDate': normalized,
        },
    }


@router.get('/stats')
def get_checkin_stats(
    child_id: int | None = None,
    days: int = 92,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """打卡统计：连续天数、累计天数、每日获得阳光、日历明细、月度汇总。

    child_id 为空时统计自己；家长可传孩子 id 查看孩子数据。
    """
    if child_id is None:
        target = current_user
    else:
        if current_user.role != 'parent':
            raise HTTPException(status_code=403, detail='无权查看该孩子数据')
        target = db.query(User).filter(
            User.pk_users == child_id,
            User.fk_users_parent == current_user.pk_users,
        ).first()
        if not target:
            raise HTTPException(status_code=404, detail='孩子账号不存在')

    days = max(7, min(days, 365))
    today = datetime.now().date()

    rows = db.query(CheckIn).filter(CheckIn.fk_users == target.pk_users).all()
    pending_rows = (
        db.query(PendingSunlight)
        .filter(PendingSunlight.fk_users == target.pk_users)
        .all()
    )
    pending_by_checkin = {
        p.fk_check_ins: p for p in pending_rows if p.fk_check_ins is not None
    }

    # 同一天可能有多条记录，按 approved > pending > rejected 取优先级最高的那条
    rank = {'approved': 3, 'pending': 2, 'rejected': 1}
    by_date: dict[date, CheckIn] = {}
    for r in rows:
        d = _parse_check_date(r.check_date)
        if not d:
            continue
        cur = by_date.get(d)
        if cur is None or rank.get(r.status, 0) > rank.get(cur.status, 0):
            by_date[d] = r

    approved_dates = {d for d, r in by_date.items() if r.status == 'approved'}
    base_streak, best_streak, display_streak = _streak_snapshot(target, db)

    start = today - timedelta(days=days - 1)
    daily = []
    for i in range(days):
        d = start + timedelta(days=i)
        r = by_date.get(d)
        status = r.status if r else 'none'
        points = r.total_points if (r and r.status == 'approved') else 0
        p = pending_by_checkin.get(r.pk_check_ins) if r else None
        daily.append({
            'date': d.isoformat(),
            'status': status,
            'points': points,
            'collected': bool(p.collected) if p else False,
            'taskCount': (len(_load_snapshot(r.completed_tasks_snapshot)) or r.task_count) if r else 0,
            'habitStepCount': r.habit_step_count if r else 0,
        })

    # 月度汇总（近 6 个月，含没有打卡的月份，前端可直接画趋势）
    monthly_map: dict[str, dict] = {}
    cursor_month = today.replace(day=1)
    month_keys: list[str] = []
    for _ in range(6):
        month_keys.append(cursor_month.strftime('%Y-%m'))
        cursor_month = (cursor_month - timedelta(days=1)).replace(day=1)
    for key in reversed(month_keys):
        monthly_map[key] = {'month': key, 'days': 0, 'sunlight': 0}
    for d, r in by_date.items():
        key = d.strftime('%Y-%m')
        if key not in monthly_map:
            continue
        monthly_map[key]['days'] += 1 if r.status in ('approved', 'pending') else 0
        if r.status == 'approved':
            monthly_map[key]['sunlight'] += r.total_points or 0
    monthly = [monthly_map[k] for k in sorted(monthly_map.keys())]

    month_prefix = today.strftime('%Y-%m')
    total_sunlight = sum(r.total_points or 0 for r in by_date.values() if r.status == 'approved')
    month_days = sum(1 for d, r in by_date.items() if r.status == 'approved' and d.strftime('%Y-%m') == month_prefix)
    month_submitted_days = sum(
        1 for d, r in by_date.items()
        if r.status in ('approved', 'pending') and d.strftime('%Y-%m') == month_prefix
    )
    month_sunlight = sum(
        r.total_points or 0 for d, r in by_date.items()
        if r.status == 'approved' and d.strftime('%Y-%m') == month_prefix
    )
    collected_sunlight = sum(p.amount for p in pending_by_checkin.values() if p.collected)
    uncollected_sunlight = sum(p.amount for p in pending_by_checkin.values() if not p.collected)

    return {
        'today': today.isoformat(),
        'todayStatus': by_date[today].status if today in by_date else 'none',
        'streakDays': display_streak,
        'approvedStreakDays': base_streak,
        'bestStreakDays': best_streak,
        'totalDays': len(approved_dates),
        'submittedDays': len(by_date),
        'monthDays': month_days,
        'monthSubmittedDays': month_submitted_days,
        'monthSunlight': month_sunlight,
        'totalSunlight': total_sunlight,
        'collectedSunlight': collected_sunlight,
        'uncollectedSunlight': uncollected_sunlight,
        'avgSunlight': round(total_sunlight / len(approved_dates), 1) if approved_dates else 0,
        'daily': daily,
        'monthly': monthly,
    }


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
        # 该打卡已有待收集阳光（含已收集）时不再重复生成，避免重复发放
        already_created = (
            db.query(PendingSunlight)
            .filter(PendingSunlight.fk_check_ins == record.pk_check_ins)
            .first()
        )
        if already_created:
            # 金额以本次审批后的分值为准（驳回后重新提交过则同步更新未收集的那条）
            if not already_created.collected and already_created.amount != record.total_points:
                already_created.amount = record.total_points
        else:
            pending = PendingSunlight(
                fk_users=child.pk_users,
                amount=record.total_points,
                reason=f'打卡审批通过（{record.check_date}）',
                fk_check_ins=record.pk_check_ins,
                collected=False,
            )
            db.add(pending)
    # 更新连续打卡天数：以今天为锚点重算，不受补打卡历史日期影响
    db.flush()
    _refresh_streak_days(child, db)
    db.commit()
    db.refresh(child)
    # Auto-unlock badges after checkin approval
    newly_unlocked = auto_unlock_badges(child, db)
    _base, _best, display_days = _streak_snapshot(child, db)
    return {
        'success': True,
        'childName': child.name,
        'awarded': record.total_points,
        'pendingSunlight': True,
        'balance': child.sunlight_points,
        'streakDays': child.streak_days,
        'displayStreakDays': display_days,
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
