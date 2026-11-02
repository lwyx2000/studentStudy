from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Badge, BadgeUnlock, CheckIn, ItemLossRecord, MistakeRecord,
    SunlightHistory, Task, User,
)

router = APIRouter()


def _norm_date_key(raw) -> str:
    """把 2026/9/1 这类写法归一成 2026-09-01，用于按天比对。"""
    if hasattr(raw, 'isoformat'):
        return raw.isoformat()
    s = str(raw or '').strip().replace('/', '-').replace('.', '-')
    parts = s.split('-')
    if len(parts) == 3:
        try:
            return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
        except ValueError:
            return s
    return s


def resolve_target(current_user: User, child_id: int | None, db: Session) -> User:
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


def _compute_requirement_progress(requirement_type: str, requirement_value: int, target: User, db: Session) -> int:
    """Return the current progress value for a given requirement type."""
    uid = target.pk_users
    if requirement_type == 'streak_days':
        return target.streak_days or 0
    elif requirement_type == 'total_sunlight':
        return target.sunlight_points or 0
    elif requirement_type == 'task_complete':
        return db.query(Task).filter(
            Task.fk_users == uid, Task.status == 'completed'
        ).count()
    elif requirement_type == 'checkin_count':
        return db.query(CheckIn).filter(
            CheckIn.fk_users == uid, CheckIn.status == 'approved'
        ).count()
    elif requirement_type == 'mistake_count':
        return db.query(MistakeRecord).filter(
            MistakeRecord.fk_users == uid
        ).count()
    elif requirement_type == 'zero_loss_days':
        # 「零丢失天数」= 已通过打卡的日期中，当天没有物品丢失记录的天数。
        # 旧实现用「审批数 − 丢失记录数」，丢失记录是累计的，会算出负数，语义也不对。
        checkin_dates = {
            _norm_date_key(r[0])
            for r in db.query(CheckIn.check_date).filter(
                CheckIn.fk_users == uid, CheckIn.status == 'approved'
            ).distinct().all()
        }
        loss_dates = {
            _norm_date_key(r[0])
            for r in db.query(ItemLossRecord.lost_date).filter(
                ItemLossRecord.fk_users == uid
            ).distinct().all()
        }
        return len(checkin_dates - loss_dates)
    elif requirement_type == 'apple_count':
        return target.apples or 0
    elif requirement_type == 'sunlight_earned_total':
        result = db.query(func.coalesce(func.sum(SunlightHistory.amount), 0)).filter(
            SunlightHistory.fk_users == uid,
            SunlightHistory.type == 'earn',
        ).scalar()
        return int(result or 0)
    else:
        return 0


def auto_unlock_badges(target: User, db: Session) -> list[dict]:
    """Check all badges against current progress and auto-unlock eligible ones.
    Returns a list of newly unlocked badge dicts.
    """
    badges = db.query(Badge).order_by(Badge.pk_badges).all()
    existing_unlocks = {
        u.fk_badges for u in
        db.query(BadgeUnlock).filter(BadgeUnlock.fk_users == target.pk_users).all()
    }
    newly_unlocked = []

    for badge in badges:
        if badge.pk_badges in existing_unlocks:
            continue

        progress = _compute_requirement_progress(
            badge.requirement_type, badge.requirement_value, target, db
        )

        if progress >= badge.requirement_value:
            # 用 ON CONFLICT DO NOTHING 抢占解锁记录：并发（如同时收集阳光与审批打卡）
            # 时只有一个请求能插入成功，从而避免重复发放勋章奖励或主键/唯一约束报错。
            result = db.execute(
                sqlite_insert(BadgeUnlock.__table__)
                .values(
                    fk_users=target.pk_users,
                    fk_badges=badge.pk_badges,
                    unlocked_at=datetime.now(),
                )
                .on_conflict_do_nothing(index_elements=['fk_users', 'fk_badges'])
            )
            if not result.rowcount:
                continue  # 已被并发请求解锁
            existing_unlocks.add(badge.pk_badges)
            if badge.reward_points:
                # 阳光值用 SQL 自增，避免并发下互相覆盖余额
                db.query(User).filter(User.pk_users == target.pk_users).update(
                    {User.sunlight_points: User.sunlight_points + badge.reward_points},
                    synchronize_session=False,
                )
                db.expire(target)
                # 记录阳光值变动历史（勋章奖励）
                reward_history = SunlightHistory(
                    fk_users=target.pk_users,
                    amount=badge.reward_points,
                    reason=f'🎖️ 解锁勋章「{badge.name}」奖励',
                    type='earn',
                )
                db.add(reward_history)
            newly_unlocked.append({
                'pk_badges': badge.pk_badges,
                'name': badge.name,
                'icon': badge.icon,
                'reward_points': badge.reward_points,
            })

    if newly_unlocked:
        db.commit()

    return newly_unlocked


@router.get('/')
def list_badges(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    badges = db.query(Badge).order_by(Badge.pk_badges).all()
    unlocks = {
        u.fk_badges: u
        for u in db.query(BadgeUnlock).filter(BadgeUnlock.fk_users == target.pk_users).all()
    }
    result = []
    for b in badges:
        unlock = unlocks.get(b.pk_badges)
        progress = _compute_requirement_progress(b.requirement_type, b.requirement_value, target, db)
        result.append({
            'pk_badges': b.pk_badges,
            'name': b.name,
            'description': b.description,
            'icon': b.icon,
            'color': b.color,
            'requirement': b.requirement,
            'requirement_type': b.requirement_type,
            'requirement_value': b.requirement_value,
            'reward_points': b.reward_points,
            'unlocked': unlock is not None,
            'unlocked_at': unlock.unlocked_at.isoformat() if unlock else None,
            'progress': min(progress, b.requirement_value),
        })
    return {'badges': result}


@router.post('/{badge_id}/unlock')
def unlock_badge(
    badge_id: int,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    existing = db.query(BadgeUnlock).filter(
        BadgeUnlock.fk_users == target.pk_users,
        BadgeUnlock.fk_badges == badge_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail='已解锁')
    badge = db.query(Badge).filter(Badge.pk_badges == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail='勋章不存在')
    # 校验解锁条件是否满足（防止孩子端直接调用 API 绕过前端限制）
    progress = _compute_requirement_progress(badge.requirement_type, badge.requirement_value, target, db)
    if progress < badge.requirement_value:
        raise HTTPException(status_code=400, detail=f'未满足解锁条件（当前进度 {progress}/{badge.requirement_value}）')
    result = db.execute(
        sqlite_insert(BadgeUnlock.__table__)
        .values(
            fk_users=target.pk_users,
            fk_badges=badge_id,
            unlocked_at=datetime.now(),
        )
        .on_conflict_do_nothing(index_elements=['fk_users', 'fk_badges'])
    )
    if not result.rowcount:
        db.rollback()
        raise HTTPException(status_code=409, detail='已解锁')
    if badge.reward_points:
        db.query(User).filter(User.pk_users == target.pk_users).update(
            {User.sunlight_points: User.sunlight_points + badge.reward_points},
            synchronize_session=False,
        )
        # 记录阳光值变动历史（手动解锁勋章奖励）
        reward_history = SunlightHistory(
            fk_users=target.pk_users,
            amount=badge.reward_points,
            reason=f'🎖️ 解锁勋章「{badge.name}」奖励',
            type='earn',
        )
        db.add(reward_history)
    db.commit()
    db.refresh(target)
    return {'success': True, 'badge': badge}


@router.post('/check-unlocks')
def check_and_unlock(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-detect and unlock badges that meet their requirements.
    Called by the frontend after key actions (checkin approval, task completion, etc.)
    """
    target = resolve_target(current_user, child_id, db)
    newly_unlocked = auto_unlock_badges(target, db)
    return {'newly_unlocked': newly_unlocked, 'total_unlocked': len(newly_unlocked)}


@router.post('/audit-and-fix-unlocks')
def audit_and_fix_unlocks(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """【家长专用】回滚不该解锁的勋章，并扣除对应阳光。
    用于修复孩子通过 bug 点击不该解锁的勋章的情况。
    对每条已有解锁记录重新校验当前条件，不满足的删除 unlock 并扣回 reward 阳光。
    """
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='只有家长可以操作')
    if not child_id:
        raise HTTPException(status_code=400, detail='必须指定孩子')
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')

    unlocks = db.query(BadgeUnlock).filter(BadgeUnlock.fk_users == child.pk_users).all()
    removed = []
    deducted_sunlight = 0
    actual_deduct = 0

    for u in unlocks:
        badge = db.query(Badge).filter(Badge.pk_badges == u.fk_badges).first()
        if not badge:
            continue
        progress = _compute_requirement_progress(badge.requirement_type, badge.requirement_value, child, db)
        if progress < badge.requirement_value:
            # 当前条件不满足 → 回滚
            if badge.reward_points:
                deducted_sunlight += badge.reward_points
            db.delete(u)
            removed.append({'id': badge.pk_badges, 'name': badge.name, 'reward': badge.reward_points})

    if deducted_sunlight > 0:
        # 扣除多发的阳光（不会低于 0）
        actual_deduct = min(deducted_sunlight, child.sunlight_points)
        child.sunlight_points -= actual_deduct
        history = SunlightHistory(
            fk_users=child.pk_users,
            amount=-actual_deduct,
            reason='🔧 修复：回滚不合条件的勋章，扣回对应的阳光奖励',
            type='spend',
        )
        db.add(history)

    db.commit()

    return {
        'removed': removed,
        'removed_count': len(removed),
        # 之前这里返回的是「扣前的余额」而不是实际扣掉的数量，前端展示会误导家长
        'sunlight_deducted': actual_deduct,
    }
