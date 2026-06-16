from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ParentSetting, User

router = APIRouter()


@router.get('/settings')
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setting = db.query(ParentSetting).filter(ParentSetting.fk_users == current_user.pk_users).first()
    if not setting:
        setting = ParentSetting(fk_users=current_user.pk_users)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return {'settings': setting}


@router.put('/settings')
def update_settings(
    difficulty_level: int | None = None,
    daily_reminder: bool | None = None,
    achievement_notification: bool | None = None,
    weekly_report: bool | None = None,
    school_sync: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setting = db.query(ParentSetting).filter(ParentSetting.fk_users == current_user.pk_users).first()
    if not setting:
        setting = ParentSetting(fk_users=current_user.pk_users)
        db.add(setting)
    if difficulty_level is not None:
        setting.difficulty_level = difficulty_level
    if daily_reminder is not None:
        setting.daily_reminder = daily_reminder
    if achievement_notification is not None:
        setting.achievement_notification = achievement_notification
    if weekly_report is not None:
        setting.weekly_report = weekly_report
    if school_sync is not None:
        setting.school_sync = school_sync
    db.commit()
    db.refresh(setting)
    return {'settings': setting}
