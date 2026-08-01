from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AppleHistory, RewardItem, SunlightHistory, User
from app.routers.badges import auto_unlock_badges

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


@router.get('/balance')
def get_balance(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    return {'balance': target.sunlight_points}


@router.get('/history')
def get_history(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    history = (
        db.query(SunlightHistory)
        .filter(SunlightHistory.fk_users == target.pk_users)
        .order_by(SunlightHistory.created_at.desc())
        .limit(100)
        .all()
    )
    return {'history': history}


@router.post('/award')
def award_points(
    amount: int,
    reason: str = '任务奖励',
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """家长给孩子发放阳光值（只有家长角色可调用）"""
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='只有家长可以发放阳光值')
    if amount == 0:
        raise HTTPException(status_code=400, detail='数量不能为 0')
    target = resolve_target(current_user, child_id, db)
    target.sunlight_points = max(0, target.sunlight_points + amount)
    history = SunlightHistory(
        fk_users=target.pk_users,
        amount=amount,
        reason=reason,
        type='earn' if amount > 0 else 'spend',
    )
    db.add(history)
    db.commit()
    # Check badge auto-unlock after points change
    newly_unlocked = auto_unlock_badges(target, db)
    return {'balance': target.sunlight_points, 'awarded': amount, 'newly_unlocked_badges': newly_unlocked}


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
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    items = (
        db.query(RewardItem)
        .filter(RewardItem.fk_users == target.pk_users)
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


# ══════════════════════════════════════════════════════════════
#  苹果相关 API
# ══════════════════════════════════════════════════════════════

SUNLIGHT_PER_APPLE = 100


@router.get('/apples')
def get_apples(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取苹果数量和苹果历史"""
    target = resolve_target(current_user, child_id, db)
    apple_history = (
        db.query(AppleHistory)
        .filter(AppleHistory.fk_users == target.pk_users)
        .order_by(AppleHistory.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        'apples': target.apples,
        'sunlightPoints': target.sunlight_points,
        'sunlightPerApple': SUNLIGHT_PER_APPLE,
        'history': apple_history,
    }


@router.post('/apples/grow')
def grow_apple(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用阳光值种出苹果（100 阳光 = 1 苹果）"""
    target = resolve_target(current_user, child_id, db)
    if target.sunlight_points < SUNLIGHT_PER_APPLE:
        raise HTTPException(status_code=400, detail=f'阳光值不足 {SUNLIGHT_PER_APPLE}，无法种出苹果')
    target.sunlight_points -= SUNLIGHT_PER_APPLE
    target.apples += 1
    # 阳光值消费记录
    sunlight_history = SunlightHistory(
        fk_users=target.pk_users,
        amount=-SUNLIGHT_PER_APPLE,
        reason='种出 1 个苹果 🍎',
        type='spend',
    )
    db.add(sunlight_history)
    # 苹果变动记录
    apple_history = AppleHistory(
        fk_users=target.pk_users,
        amount=1,
        reason='阳光兑换苹果',
        type='grow',
    )
    db.add(apple_history)
    db.commit()
    # Check badge auto-unlock after growing apple
    newly_unlocked = auto_unlock_badges(target, db)
    return {
        'success': True,
        'apples': target.apples,
        'sunlightPoints': target.sunlight_points,
        'newly_unlocked_badges': newly_unlocked,
    }


@router.post('/apples/redeem')
def redeem_apple(
    count: int = 1,
    reason: str = '兑换奖励',
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兑换苹果（1 苹果 = 1 元）"""
    if count <= 0:
        raise HTTPException(status_code=400, detail='兑换数量必须大于 0')
    target = resolve_target(current_user, child_id, db)
    if target.apples < count:
        raise HTTPException(status_code=400, detail='苹果数量不足')
    target.apples -= count
    # 苹果变动记录
    apple_history = AppleHistory(
        fk_users=target.pk_users,
        amount=-count,
        reason=reason or f'兑换 {count} 元',
        type='redeem',
    )
    db.add(apple_history)
    db.commit()
    return {
        'success': True,
        'apples': target.apples,
        'redeemed': count,
    }
