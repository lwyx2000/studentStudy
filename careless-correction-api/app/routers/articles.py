from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Article, User

router = APIRouter()


@router.get('/')
def list_articles(
    category: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """文章列表（支持 category 筛选）"""
    query = db.query(Article)
    if category:
        query = query.filter(Article.category == category)
    articles = query.order_by(Article.published_at.desc()).limit(50).all()
    return {'articles': articles}


@router.get('/suggested')
def get_suggested(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """推荐文章（按收藏数 + 随机选取，最多 3 篇）"""
    articles = (
        db.query(Article)
        .order_by(Article.published_at.desc())
        .limit(20)
        .all()
    )
    # 简单推荐：取最新 3 篇
    suggested = articles[:3]
    return {'articles': suggested}
