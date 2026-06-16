from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ItemLossRecord, ItemStorageRecord, User

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


@router.get('/loss')
def get_loss_list(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    records = (
        db.query(ItemLossRecord)
        .filter(ItemLossRecord.fk_users == target.pk_users)
        .order_by(ItemLossRecord.created_at.desc())
        .all()
    )
    return {'records': records}


@router.post('/loss')
def report_loss(
    item_name: str,
    lost_location: str,
    estimated_cost: float = 0,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    existing = db.query(ItemLossRecord).filter(
        ItemLossRecord.fk_users == target.pk_users,
        ItemLossRecord.item_name == item_name,
    ).first()
    if existing:
        existing.frequency_30d += 1
        existing.lost_date = date.today()
        existing.lost_location = lost_location
        existing.estimated_cost = estimated_cost
        existing.is_high_frequency = existing.frequency_30d >= 3
        db.commit()
        db.refresh(existing)
        return {'record': existing}
    record = ItemLossRecord(
        fk_users=target.pk_users,
        item_name=item_name,
        lost_location=lost_location,
        estimated_cost=estimated_cost,
        lost_date=date.today(),
        is_high_frequency=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'record': record}


@router.get('/stats')
def get_loss_stats(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    records = (
        db.query(ItemLossRecord)
        .filter(ItemLossRecord.fk_users == target.pk_users)
        .all()
    )
    total_loss = len(records)
    total_cost = sum(r.estimated_cost * r.frequency_30d for r in records)
    high_freq = [
        {'itemName': r.item_name, 'frequency': r.frequency_30d}
        for r in records if r.is_high_frequency
    ]
    return {'stats': {'totalLoss': total_loss, 'totalCost': total_cost, 'highFrequencyItems': high_freq}}


@router.post('/storage', status_code=201)
def add_storage(
    item_name: str,
    storage_location: str,
    notes: str | None = None,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    record = ItemStorageRecord(
        fk_users=target.pk_users,
        item_name=item_name,
        storage_location=storage_location,
        notes=notes,
        storage_date=date.today(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'record': record}


@router.get('/storage')
def get_storage_list(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    records = (
        db.query(ItemStorageRecord)
        .filter(ItemStorageRecord.fk_users == target.pk_users)
        .order_by(ItemStorageRecord.created_at.desc())
        .all()
    )
    return {'records': records}
