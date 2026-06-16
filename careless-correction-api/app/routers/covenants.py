from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Covenant, User

router = APIRouter()


@router.get('/')
def list_covenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    covenants = (
        db.query(Covenant)
        .filter((Covenant.fk_users_child == current_user.pk_users) | (Covenant.fk_users_parent == current_user.pk_users))
        .order_by(Covenant.created_at.desc())
        .all()
    )
    return {'covenants': covenants}


@router.post('/', status_code=201)
def create_covenant(
    goal: str,
    reward: str,
    reward_type: str = 'experience',
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    covenant = Covenant(
        fk_users_child=child_id or current_user.pk_users,
        fk_users_parent=current_user.pk_users,
        goal=goal,
        reward=reward,
        reward_type=reward_type,
    )
    db.add(covenant)
    db.commit()
    db.refresh(covenant)
    return {'covenant': covenant}
