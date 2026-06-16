from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import CommunityPost, User

router = APIRouter()


@router.get('/posts')
def get_posts(
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = 20
    offset = (page - 1) * limit
    posts = (
        db.query(CommunityPost)
        .order_by(CommunityPost.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {'posts': posts, 'page': page}


@router.post('/posts', status_code=201)
def create_post(
    title: str,
    content: str = '',
    tags: dict | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = CommunityPost(
        fk_users_author=current_user.pk_users,
        title=title,
        content=content,
        tags=tags,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {'post': post}
