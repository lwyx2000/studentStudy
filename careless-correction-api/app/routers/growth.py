from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    DiagnosticAlert, GrowthSnapshot, HabitSOP, ItemLossRecord,
    MistakeRecord, Task, User,
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


@router.post('/assessment')
async def trigger_assessment(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import LlmConfig
    from app.services.growth import generate_assessment_prompt
    from app.services.llm import call_llm

    target = resolve_target(current_user, child_id, db)

    # LLM config 属于家长
    config_user_id = current_user.pk_users if current_user.role == 'parent' else (
        db.query(User).filter(User.pk_users == target.fk_users_parent).first().pk_users
        if target.fk_users_parent else current_user.pk_users
    )
    config = db.query(LlmConfig).filter(LlmConfig.fk_users == config_user_id).first()
    if not config or not config.enabled:
        raise HTTPException(status_code=400, detail='LLM 未配置或未启用')

    mistake_count = db.query(func.count(MistakeRecord.pk_mistake_records)).filter(
        MistakeRecord.fk_users == target.pk_users,
    ).scalar() or 0

    task_stats = db.query(
        func.count(Task.pk_tasks).filter(Task.status == 'completed').label('done'),
        func.count(Task.pk_tasks).label('total'),
    ).filter(Task.fk_users == target.pk_users).first()
    done = task_stats.done or 0
    total = task_stats.total or 1

    loss_count = db.query(func.coalesce(func.sum(ItemLossRecord.frequency_30d), 0)).filter(
        ItemLossRecord.fk_users == target.pk_users,
    ).scalar() or 0

    habit = db.query(HabitSOP).order_by(HabitSOP.created_at.desc()).first()
    prompt = generate_assessment_prompt(
        mistake_count=mistake_count,
        completion_rate=round(done / total * 100),
        item_loss_count=loss_count,
        habit_title=habit.title if habit else '未设置',
    )
    result = await call_llm(config, prompt)
    return {'assessment': result}


@router.get('/trend')
def get_trend(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    snapshots = (
        db.query(GrowthSnapshot)
        .filter(GrowthSnapshot.fk_users == target.pk_users)
        .order_by(GrowthSnapshot.snapshot_date)
        .all()
    )
    return {'trend': snapshots}


@router.get('/report')
def get_report(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    snapshot = (
        db.query(GrowthSnapshot)
        .filter(GrowthSnapshot.fk_users == target.pk_users)
        .order_by(GrowthSnapshot.snapshot_date.desc())
        .first()
    )
    alerts = (
        db.query(DiagnosticAlert)
        .filter(DiagnosticAlert.fk_users == target.pk_users)
        .order_by(DiagnosticAlert.created_at.desc())
        .limit(5)
        .all()
    )
    return {'report': snapshot, 'alerts': alerts}


@router.get('/alerts')
def get_alerts(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    alerts = (
        db.query(DiagnosticAlert)
        .filter(DiagnosticAlert.fk_users == target.pk_users)
        .order_by(DiagnosticAlert.created_at.desc())
        .all()
    )
    return {'alerts': alerts}
