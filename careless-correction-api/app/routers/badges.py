from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Badge, BadgeUnlock, User

router = APIRouter()


@router.get('/')
def list_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    badges = db.query(Badge).order_by(Badge.pk_badges).all()
    unlocks = {
        u.fk_badges: u
        for u in db.query(BadgeUnlock).filter(BadgeUnlock.fk_users == current_user.pk_users).all()
    }
    result = []
    for b in badges:
        unlock = unlocks.get(b.pk_badges)
        result.append({
            'pk_badges': b.pk_badges,
            'name': b.name,
            'description': b.description,
            'icon': b.icon,
            'color': b.color,
            'requirement': b.requirement,
            'reward_points': b.reward_points,
            'unlocked': unlock is not None,
            'unlocked_at': unlock.unlocked_at.isoformat() if unlock else None,
        })
    return {'badges': result}


@router.post('/{badge_id}/unlock')
def unlock_badge(
    badge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(BadgeUnlock).filter(
        BadgeUnlock.fk_users == current_user.pk_users,
        BadgeUnlock.fk_badges == badge_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail='已解锁')
    unlock = BadgeUnlock(fk_users=current_user.pk_users, fk_badges=badge_id)
    db.add(unlock)
    badge = db.query(Badge).filter(Badge.pk_badges == badge_id).first()
    if badge and badge.reward_points:
        current_user.sunlight_points += badge.reward_points
    db.commit()
    return {'success': True, 'badge': badge}
