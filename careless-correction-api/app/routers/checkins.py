from datetime import date, datetime, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import CheckIn, HabitSOP, PendingSunlight, Task, User
from app.routers.badges import auto_unlock_badges
from app.routers.tasks import _matches_week_day
from app.schemas import TaskOut

router = APIRouter()

# 与前端 HabitPrintableCenter.vue 保持一致
OPTIONAL_BONUS_POINTS = 2
ALL_DONE_BONUS_POINTS = 10


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
    """今天是否已经提交过打卡（待审批也算，已驳回不算）。

    启动迁移会把历史 check_date 全部归一成 YYYY-MM-DD，因此这里可以直接用
    等值查询（走 ix_check_ins_user_date 索引），不必把整张表读进内存再逐个解析。
    """
    today = datetime.now().date()
    row = (
        db.query(CheckIn.pk_check_ins)
        .filter(
            CheckIn.fk_users == child_id,
            CheckIn.status.in_(['pending', 'approved']),
            CheckIn.check_date == today.isoformat(),
        )
        .first()
    )
    return row is not None


def _streak_snapshot(child: User, db: Session, include_today_pending: bool = True):
    """返回 (当前连续天数, 历史最佳连续天数, 含今日待审批的展示天数, 今日是否已提交)。

    streak_days 以「今天/昨天」为锚点动态计算，因此补打卡历史日期不会把已有连击覆盖掉。
    今日是否已提交一并返回，避免调用方再查一次库。
    """
    approved = _approved_dates(child.pk_users, db)
    today = datetime.now().date()
    base = _calc_streak(approved, today)
    checked_today = _has_checked_today(child.pk_users, db)
    display = base
    if include_today_pending and today not in approved and checked_today:
        display = base + 1
    best = max(_calc_best_streak(approved), display)
    return base, best, display, checked_today


def _refresh_streak_days(child: User, db: Session) -> int:
    """刷新并回写连续打卡天数（仅统计已通过审批的记录）。"""
    base, _best, _display, _checked = _streak_snapshot(child, db, include_today_pending=False)
    child.streak_days = base
    return base


def _sanitize_completed_tasks_snapshot(raw) -> list[dict]:
    """清洗前端传来的完成项快照：只保留 title/icon/points/subTaskId，限制数量与长度。

    raw 可以是 JSON 字符串（旧客户端的 query 参数）或已经解析好的列表（新客户端 JSON body）。
    """
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        if not isinstance(data, list):
            return []
        cleaned: list[dict] = []
        seen: set[str] = set()
        for item in data[:100]:
            if not isinstance(item, dict):
                continue
            title = str(item.get('title', ''))[:100].strip()
            if not title:
                continue
            # 子任务 id 用于精确计分：同名小任务分属不同主任务时不会互相顶掉
            sid = str(item.get('subTaskId') or item.get('sub_task_id') or '').strip()[:20]
            key = f'id:{sid}' if sid else f'title:{title}'
            if key in seen:
                # 同一条小任务重复提交（客户端连点或伪造请求）只计一次，
                # 否则把同一项复制 N 遍就能拿到 N 倍阳光值
                continue
            seen.add(key)
            cleaned.append({
                'title': title,
                'icon': str(item.get('icon', ''))[:10],
                'points': max(0, min(9999, int(item.get('points', 0) or 0))),
                'subTaskId': sid,
            })
        return cleaned
    except Exception:
        return []


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
    """提交打卡（query 参数版，保留给已安装的旧客户端）。"""
    return _submit_checkin(
        db=db,
        current_user=current_user,
        check_date=check_date,
        total_points=total_points,
        habit_step_count=habit_step_count,
        task_count=task_count,
        required_points=required_points,
        optional_bonus=optional_bonus,
        all_done_bonus=all_done_bonus,
        habit_points=habit_points,
        completed_tasks=completed_tasks,
    )


class CheckinSubmitIn(BaseModel):
    check_date: str
    total_points: int = 0
    habit_step_count: int = 0
    task_count: int = 0
    required_points: int = 0
    optional_bonus: int = 0
    all_done_bonus: int = 0
    habit_points: int = 0
    # 直接收数组：走 query string 时中文标题 percent-encode 后会膨胀数倍，
    # 清单多几项就可能撞上 nginx 的 8KB 请求行上限（414），打卡直接失败
    completed_tasks: list[dict] | None = None


@router.post('/submit')
def submit_checkin_json(
    payload: CheckinSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交打卡（JSON body 版，前端使用）。"""
    return _submit_checkin(
        db=db,
        current_user=current_user,
        check_date=payload.check_date,
        total_points=payload.total_points,
        habit_step_count=payload.habit_step_count,
        task_count=payload.task_count,
        required_points=payload.required_points,
        optional_bonus=payload.optional_bonus,
        all_done_bonus=payload.all_done_bonus,
        habit_points=payload.habit_points,
        completed_tasks=payload.completed_tasks,
    )


def _submit_checkin(
    *,
    db: Session,
    current_user: User,
    check_date: str,
    total_points: int = 0,
    habit_step_count: int = 0,
    task_count: int = 0,
    required_points: int = 0,
    optional_bonus: int = 0,
    all_done_bonus: int = 0,
    habit_points: int = 0,
    completed_tasks=None,
) -> dict:
    normalized = _normalize_check_date(check_date)
    if not normalized:
        raise HTTPException(status_code=400, detail='打卡日期格式无效')
    # 不允许给未来日期打卡（避免提前刷阳光、污染连续天数统计）
    if _parse_check_date(normalized) > datetime.now().date():
        raise HTTPException(status_code=400, detail='不能给未来日期打卡')

    # ── 服务端计分：按数据库真实分值重算，不信任客户端传来的分值与分值明细 ──
    # 之前只做「不太精确的理论上限」夹取，孩子改包即可把 reward_points 抬到上限，
    # 且快照里的单项分值会被原样展示给家长。这里改为逐项核对数据库。
    total_points = max(0, total_points)
    habit_points = max(0, habit_points)

    check_date_obj = _parse_check_date(normalized) or datetime.now().date()
    tasks = (
        db.query(Task)
        .options(selectinload(Task.sub_tasks))
        .filter(Task.fk_users == current_user.pk_users, Task.active == True)
        .all()
    )
    # 当天「必做小任务」总数，用于服务端判定全部完成奖励
    today_required = 0
    subtask_by_id: dict[str, tuple[int, bool]] = {}
    subtask_by_title: dict[str, tuple[int, bool]] = {}
    for t in tasks:
        if not _matches_week_day(t.week_day, check_date_obj):
            continue
        for s in t.sub_tasks:
            if not _matches_week_day(s.week_day, check_date_obj):
                continue
            pts = s.reward_points if s.reward_points is not None else (
                OPTIONAL_BONUS_POINTS if s.is_optional else (t.reward_points or 0)
            )
            entry = (max(0, min(int(pts), 999)), bool(s.is_optional))
            # 精确索引：不同主任务下同名的小任务分值可能不同，按 id 才能算对
            subtask_by_id[str(s.pk_sub_tasks)] = entry
            # 兜底索引：旧客户端只传标题，同名以先出现的为准（与前端列表顺序一致）
            subtask_by_title.setdefault(s.title.strip(), entry)
            if not s.is_optional:
                today_required += 1

    # 习惯计分与前端口径一致：每勾选一步 = 该习惯完整分值（分值 × 步骤数）
    habits = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.fk_users == current_user.pk_users, HabitSOP.active == True)
        .all()
    )
    habit_sum = sum((h.reward_points or 0) * len(h.steps) for h in habits)
    habit_points = min(habit_points, habit_sum)
    # 习惯步数同样以数据库为准，避免客户端塞一个夸张数字污染家长端的「完成习惯步骤」
    max_steps = sum(len(h.steps) for h in habits)
    habit_step_count = max(0, min(habit_step_count, max_steps))

    snapshot_items = _sanitize_completed_tasks_snapshot(completed_tasks)

    if snapshot_items:
        required_sum = 0
        optional_count = 0
        matched_required = 0
        fixed_items: list[dict] = []
        # 已计入的小任务（按 id / 标题归一）：同一条小任务无论出现几次都只计一次分
        counted: set[str] = set()
        for item in snapshot_items:
            title = str(item.get('title', '')).strip()
            sid = str(item.get('subTaskId') or '').strip()
            hit = subtask_by_id.get(sid) if sid else None
            if hit is None:
                hit = subtask_by_title.get(title)
                counter_key = f'title:{title}'
            else:
                counter_key = f'id:{sid}'
            if hit is None or counter_key in counted:
                # 数据库里找不到对应小任务（已被删除或客户端伪造），或重复提交 → 不计分
                fixed_items.append({**item, 'points': 0, 'verified': False})
                continue
            counted.add(counter_key)
            pts, is_optional = hit
            if is_optional:
                optional_count += 1
                fixed_items.append({**item, 'points': OPTIONAL_BONUS_POINTS, 'verified': True})
            else:
                required_sum += pts
                matched_required += 1
                fixed_items.append({**item, 'points': pts, 'verified': True})

        all_done = today_required > 0 and matched_required >= today_required
        all_done_bonus = ALL_DONE_BONUS_POINTS if all_done else 0
        optional_bonus = optional_count * OPTIONAL_BONUS_POINTS
        required_points = required_sum
        cap = required_sum + optional_bonus + all_done_bonus + habit_points
        total_points = min(total_points, cap)
        snapshot = json.dumps(fixed_items, ensure_ascii=False) if fixed_items else None
    else:
        # 无快照（旧客户端）：沿用理论上限夹取
        task_sum = sum(t.reward_points or 0 for t in tasks)
        subtask_sum = sum(
            (
                s.reward_points if s.reward_points is not None
                else (OPTIONAL_BONUS_POINTS if s.is_optional else (t.reward_points or 0))
            )
            for t in tasks for s in t.sub_tasks
        )
        max_possible = max(task_sum, subtask_sum) + habit_sum + 110
        total_points = min(total_points, max_possible)
        required_points = max(0, min(required_points, total_points))
        optional_bonus = max(0, min(optional_bonus, 100))
        all_done_bonus = max(0, min(all_done_bonus, 10))
        snapshot = None

    # 快照非空时，完成任务数以快照条目数为准，避免与家长看到的明细条数不一致
    if snapshot_items:
        task_count = len(snapshot_items)

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
        base, best, display, checked_today = _streak_snapshot(current_user, db)
        return {
            # 统一用 camelCase 序列化（与 /mine、/details 一致），否则同一个对象
            # 在不同接口下字段名不一样，前端只能靠猜
            'checkin': _checkin_to_dict(existing, current_user),
            'updated': True,
            'streak': {
                'days': display,
                'approvedDays': base,
                'bestDays': best,
                'checkedToday': checked_today,
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
    base, best, display, checked_today = _streak_snapshot(current_user, db)
    return {
        'checkin': _checkin_to_dict(record, current_user),
        'updated': False,
        'streak': {
            'days': display,
            'approvedDays': base,
            'bestDays': best,
            'checkedToday': checked_today,
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
    base_streak, best_streak, display_streak, _checked = _streak_snapshot(target, db)

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
    collected_sunlight = sum(p.amount for p in pending_rows if p.collected)
    # 未收集的要算上所有来源：家长手动发放的阳光不关联打卡（fk_check_ins 为空），
    # 只统计 pending_by_checkin 会让「待收集」总额比阳光树页面实际显示的少
    uncollected_sunlight = sum(p.amount for p in pending_rows if not p.collected)

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

    # 条件更新「抢占」这次审批：并发重复点击时只有一个请求真正通过，
    # 避免同一条打卡被审批两次、生成两份待收集阳光。
    approved_at = datetime.now()
    claimed = (
        db.query(CheckIn)
        .filter(
            CheckIn.pk_check_ins == checkin_id,
            CheckIn.status.in_(['pending', 'rejected']),
        )
        .update(
            {
                CheckIn.status: 'approved',
                CheckIn.approved_at: approved_at,
                CheckIn.reject_reason: None,
            },
            synchronize_session=False,
        )
    )
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=400, detail='该打卡已审批')

    # 不再直接增加 sunlight_points，而是生成「待收集阳光」记录
    # 孩子需在阳光树页面点击收集后才正式变为阳光值
    if record.total_points > 0:
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
            # 唯一索引 uq_pending_sunlight_checkin 兜底：并发下第二条自动忽略
            db.execute(
                sqlite_insert(PendingSunlight)
                .values(
                    fk_users=child.pk_users,
                    amount=record.total_points,
                    reason=f'打卡审批通过（{record.check_date}）',
                    fk_check_ins=record.pk_check_ins,
                    collected=False,
                    created_at=approved_at,
                )
                .on_conflict_do_nothing(index_elements=['fk_check_ins'])
            )
    # 更新连续打卡天数：以今天为锚点重算，不受补打卡历史日期影响
    db.flush()
    _refresh_streak_days(child, db)
    db.commit()
    db.refresh(record)
    db.refresh(child)
    # Auto-unlock badges after checkin approval
    newly_unlocked = auto_unlock_badges(child, db)
    _base, _best, display_days, _checked = _streak_snapshot(child, db)
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
    reject_reason = (reason or '').strip()[:500] or None
    # 条件更新：与 approve 并发时只有一方生效
    claimed = (
        db.query(CheckIn)
        .filter(CheckIn.pk_check_ins == checkin_id, CheckIn.status == 'pending')
        .update(
            {CheckIn.status: 'rejected', CheckIn.reject_reason: reject_reason},
            synchronize_session=False,
        )
    )
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=400, detail='该打卡已审批')
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
