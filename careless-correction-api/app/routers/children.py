from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, require_parent
from app.database import get_db
from app.models import User
from app.schemas import ChildOut, TokenOut

router = APIRouter()


@router.get('/', response_model=list[ChildOut])
def list_children(
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """获取家长名下所有孩子"""
    children = db.query(User).filter(
        User.fk_users_parent == current_user.pk_users,
        User.role == 'child',
    ).order_by(User.created_at).all()
    return [ChildOut.model_validate(c) for c in children]


@router.post('/', response_model=ChildOut, status_code=201)
def add_child(
    name: str,
    grade: int = 3,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """家长添加孩子账号"""
    existing = db.query(User).filter(
        User.name == name,
        User.fk_users_parent == current_user.pk_users,
        User.role == 'child',
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail='已存在同名孩子')
    child = User(
        name=name,
        role='child',
        grade=grade,
        fk_users_parent=current_user.pk_users,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return ChildOut.model_validate(child)


@router.put('/{child_id}', response_model=ChildOut)
def update_child(
    child_id: int,
    name: str | None = None,
    grade: int | None = None,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """更新孩子信息"""
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    if name is not None:
        child.name = name
    if grade is not None:
        child.grade = grade
    db.commit()
    db.refresh(child)
    return ChildOut.model_validate(child)


@router.delete('/{child_id}')
def delete_child(
    child_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """删除孩子账号及其所有数据"""
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    db.delete(child)
    db.commit()
    return {'success': True}


@router.post('/{child_id}/switch-token', response_model=TokenOut)
def switch_to_child(
    child_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """家长获取孩子视角的 token（用于查看孩子端）"""
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    from app.schemas import UserOut
    token = create_access_token(child.pk_users, child.role)
    return TokenOut(token=token, user=UserOut.model_validate(child))
