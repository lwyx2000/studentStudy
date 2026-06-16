from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import RewardItem, SunlightHistory, User

router = APIRouter()


@router.get('/balance')
def get_balance(current_user: User = Depends(get_current_user)):
    return {'balance': current_user.sunlight_points}


@router.get('/history')
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(SunlightHistory)
        .filter(SunlightHistory.fk_users == current_user.pk_users)
        .order_by(SunlightHistory.created_at.desc())
        .limit(100)
        .all()
    )
    return {'history': history}


@router.post('/redeem')
def redeem(
    reward_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(RewardItem).filter(
        RewardItem.pk_reward_items == reward_item_id,
        RewardItem.active == True,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail='兑换物品不存在或已禁用')
    if current_user.sunlight_points < item.cost:
        raise HTTPException(status_code=400, detail='阳光值不足')
    current_user.sunlight_points -= item.cost
    history = SunlightHistory(
        fk_users=current_user.pk_users,
        amount=-item.cost,
        reason=f'兑换：{item.name}',
        type='spend',
    )
    db.add(history)
    db.commit()
    return {'success': True, 'pointsSpent': item.cost, 'itemName': item.name}


@router.get('/rewards')
def get_rewards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(RewardItem)
        .filter(RewardItem.fk_users == current_user.pk_users)
        .order_by(RewardItem.cost)
        .all()
    )
    return {'rewards': items}


@router.post('/rewards', status_code=201)
def create_reward(
    name: str,
    cost: int,
    description: str | None = None,
    icon: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = RewardItem(fk_users=current_user.pk_users, name=name, cost=cost, description=description, icon=icon)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {'reward': item}


@router.put('/rewards/{reward_id}')
def update_reward(
    reward_id: int,
    name: str | None = None,
    description: str | None = None,
    cost: int | None = None,
    icon: str | None = None,
    active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(RewardItem).filter(
        RewardItem.pk_reward_items == reward_id,
        RewardItem.fk_users == current_user.pk_users,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail='物品不存在')
    if name is not None:
        item.name = name
    if description is not None:
        item.description = description
    if cost is not None:
        item.cost = cost
    if icon is not None:
        item.icon = icon
    if active is not None:
        item.active = active
    db.commit()
    db.refresh(item)
    return {'reward': item}


@router.delete('/rewards/{reward_id}')
def delete_reward(
    reward_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(RewardItem).filter(
        RewardItem.pk_reward_items == reward_id,
        RewardItem.fk_users == current_user.pk_users,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail='物品不存在')
    db.delete(item)
    db.commit()
    return {'success': True}
