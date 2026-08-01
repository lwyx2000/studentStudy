from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ItemLossRecord, ItemStorageRecord, User


# ── 高频丢失建议模板 ──
_LOSS_SUGGESTIONS = {
    '文具': '建议用文具盒固定收纳位置，贴上姓名贴，用完即归位。',
    '水壶': '建议选一个固定挂钩挂在书包侧袋，离座前检查。',
    '雨伞': '建议在校内设固定伞架位，写上名字，下雨后及时取回。',
    '校服': '建议在校服内标签处写上班级和姓名，体育课后统一收纳。',
    '书本': '建议用不同颜色的书套区分科目，每天睡前检查书包清单。',
    '作业': '建议作业完成后立即放入对应科目文件夹，不要随意摆放。',
    '钥匙': '建议用挂绳固定在书包拉链上，养成离位必摸口袋的习惯。',
    '默认': '建议贴上荧光姓名贴，固定收纳位置，离座前做「回头看一眼」检查。',
}


def _get_suggestion(item_name: str) -> str:
    for key, suggestion in _LOSS_SUGGESTIONS.items():
        if key in item_name:
            return suggestion
    return _LOSS_SUGGESTIONS['默认']

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
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    existing = db.query(ItemLossRecord).filter(
        ItemLossRecord.fk_users == target.pk_users,
        ItemLossRecord.item_name == item_name,
    ).first()

    if existing:
        # 如果上次丢失超过30天了，重置频率计数
        if existing.lost_date and existing.lost_date < thirty_days_ago:
            existing.frequency_30d = 1
        else:
            existing.frequency_30d += 1
        existing.lost_date = today
        existing.lost_location = lost_location
        existing.estimated_cost = estimated_cost
        existing.is_high_frequency = existing.frequency_30d >= 3
        existing.suggestion = _get_suggestion(item_name) if existing.is_high_frequency else None
        db.commit()
        db.refresh(existing)
        return {'record': existing}

    record = ItemLossRecord(
        fk_users=target.pk_users,
        item_name=item_name,
        lost_location=lost_location,
        estimated_cost=estimated_cost,
        lost_date=today,
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


@router.delete('/loss/{record_id}')
def delete_loss_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ItemLossRecord).filter(ItemLossRecord.pk_item_loss_records == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')
    target = resolve_target(current_user, None, db)
    if record.fk_users != target.pk_users:
        raise HTTPException(status_code=403, detail='无权操作')
    db.delete(record)
    db.commit()
    return {'success': True}


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


@router.delete('/storage/{record_id}')
def delete_storage_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ItemStorageRecord).filter(ItemStorageRecord.pk_item_storage_records == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')
    target = resolve_target(current_user, None, db)
    if record.fk_users != target.pk_users:
        raise HTTPException(status_code=403, detail='无权操作')
    db.delete(record)
    db.commit()
    return {'success': True}
