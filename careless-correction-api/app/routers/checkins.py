from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import CheckIn, SunlightHistory, User
from app.routers.badges import auto_unlock_badges


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


def _update_streak_days(child: User, db: Session, check_date: str):
    """根据打卡日期更新连续打卡天数（计入本次通过的打卡）。"""
    current = _parse_check_date(check_date) or datetime.now().date()

    # 收集该孩子所有已通过打卡的日期（含本次，因为调用前 status 已置为 approved 且 autoflush 生效）
    prev = (
        db.query(CheckIn)
        .filter(
            CheckIn.fk_users == child.pk_users,
            CheckIn.status == 'approved',
        )
        .order_by(CheckIn.pk_check_ins.desc())
        .limit(400)
        .all()
    )
    dates = {_parse_check_date(p.check_date) for p in prev}
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

router = APIRouter()


@router.post('/')
def submit_checkin(
    check_date: str,
    total_points: int = 0,
    habit_step_count: int = 0,
    task_count: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(CheckIn).filter(
        CheckIn.fk_users == current_user.pk_users,
        CheckIn.check_date == check_date,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail='该日期已提交过打卡')
    record = CheckIn(
        fk_users=current_user.pk_users,
        check_date=check_date,
        total_points=total_points,
        habit_step_count=habit_step_count,
        task_count=task_count,
        status='pending',
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'checkin': record}


@router.get('/pending')
def list_pending_checkins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(CheckIn)
        .join(User, CheckIn.fk_users == User.pk_users)
        .filter(
            User.fk_users_parent == current_user.pk_users,
            CheckIn.status == 'pending',
        )
        .order_by(CheckIn.created_at.desc())
        .all()
    )
    result = []
    for r in records:
        child = db.query(User).filter(User.pk_users == r.fk_users).first()
        result.append({
            'id': r.pk_check_ins,
            'childId': r.fk_users,
            'childName': child.name if child else '未知',
            'checkDate': r.check_date,
            'totalPoints': r.total_points,
            'habitStepCount': r.habit_step_count,
            'taskCount': r.task_count,
            'status': r.status,
            'createdAt': r.created_at.isoformat() if r.created_at else None,
        })
    return {'pending': result}


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
    if record.status != 'pending':
        raise HTTPException(status_code=400, detail='该打卡已审批')
    record.status = 'approved'
    record.approved_at = datetime.now()
    child.sunlight_points += record.total_points
    # 记录阳光值变动历史
    if record.total_points > 0:
        history = SunlightHistory(
            fk_users=child.pk_users,
            amount=record.total_points,
            reason=f'打卡审批通过（{record.check_date}）',
            type='earn',
        )
        db.add(history)
    # 更新连续打卡天数
    _update_streak_days(child, db, record.check_date)
    db.commit()
    # Auto-unlock badges after checkin approval
    newly_unlocked = auto_unlock_badges(child, db)
    return {
        'success': True,
        'childName': child.name,
        'awarded': record.total_points,
        'balance': child.sunlight_points,
        'streakDays': child.streak_days,
        'newly_unlocked_badges': newly_unlocked,
    }


@router.post('/{checkin_id}/reject')
def reject_checkin(
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
    if record.status != 'pending':
        raise HTTPException(status_code=400, detail='该打卡已审批')
    record.status = 'rejected'
    db.commit()
    return {'success': True, 'childName': child.name}
