from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Badge, BadgeUnlock, CheckIn, ItemLossRecord, MistakeRecord,
    SunlightHistory, Task, User,
)

router = APIRouter()


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
        # Count approved checkins with zero item loss on that date
        return db.query(CheckIn).filter(
            CheckIn.fk_users == uid,
            CheckIn.status == 'approved',
        ).count() - db.query(ItemLossRecord).filter(
            ItemLossRecord.fk_users == uid
        ).count()
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
            unlock = BadgeUnlock(
                fk_users=target.pk_users,
                fk_badges=badge.pk_badges,
            )
            db.add(unlock)
            if badge.reward_points:
                target.sunlight_points += badge.reward_points
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
    unlock = BadgeUnlock(fk_users=target.pk_users, fk_badges=badge_id)
    db.add(unlock)
    badge = db.query(Badge).filter(Badge.pk_badges == badge_id).first()
    if badge and badge.reward_points:
        target.sunlight_points += badge.reward_points
    db.commit()
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
