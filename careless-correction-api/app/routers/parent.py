from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ParentSetting, User

router = APIRouter()


def _get_or_create_setting(db: Session, user_id: int) -> ParentSetting:
    """fk_users 有唯一约束：并发首次加载时两个请求同时 INSERT 会撞约束，
    这里捕获后回滚重查（对方事务已提交，重查必命中）。"""
    setting = db.query(ParentSetting).filter(ParentSetting.fk_users == user_id).first()
    if setting:
        return setting
    setting = ParentSetting(fk_users=user_id)
    db.add(setting)
    try:
        db.commit()
        db.refresh(setting)
        return setting
    except IntegrityError:
        db.rollback()
        setting = db.query(ParentSetting).filter(ParentSetting.fk_users == user_id).first()
        if not setting:
            raise
        return setting


@router.get('/settings')
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setting = _get_or_create_setting(db, current_user.pk_users)
    return {'settings': setting}


@router.put('/settings')
def update_settings(
    daily_reminder: bool | None = None,
    achievement_notification: bool | None = None,
    weekly_report: bool | None = None,
    school_sync: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setting = _get_or_create_setting(db, current_user.pk_users)
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
