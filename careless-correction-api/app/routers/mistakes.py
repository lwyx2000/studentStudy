from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import MistakeRecord, MistakeReview, User

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


@router.post('/upload')
async def upload_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    from pathlib import Path
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f'mistake_{datetime.now().timestamp()}_{image.filename}'
    content = await image.read()
    file_path.write_bytes(content)
    return {'imageUrl': f'/uploads/{file_path.name}'}


@router.post('/', status_code=201)
def create_mistake(
    subject: str,
    image_url: str,
    is_carelessness: bool = True,
    category: str | None = None,
    knowledge_point: str | None = None,
    grade: int | None = None,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    record = MistakeRecord(
        fk_users=target.pk_users,
        subject=subject,
        image_url=image_url,
        is_carelessness=is_carelessness,
        category=category,
        knowledge_point=knowledge_point,
        grade=grade,
        next_review_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'record': record}


@router.get('/')
def list_mistakes(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    records = (
        db.query(MistakeRecord)
        .filter(MistakeRecord.fk_users == target.pk_users)
        .order_by(MistakeRecord.created_at.desc())
        .all()
    )
    return {'records': records}


@router.delete('/{record_id}')
def delete_mistake(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(MistakeRecord).filter(
        MistakeRecord.pk_mistake_records == record_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')
    # 本人或其家长可删除
    if record.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == record.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')
    db.delete(record)
    db.commit()
    return {'success': True}


@router.get('/due')
def get_due_reviews(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取到期需要复习的错题"""
    target = resolve_target(current_user, child_id, db)
    now = datetime.now()
    records = (
        db.query(MistakeRecord)
        .filter(
            MistakeRecord.fk_users == target.pk_users,
            MistakeRecord.resolved == False,
            MistakeRecord.next_review_at <= now,
        )
        .order_by(MistakeRecord.next_review_at)
        .all()
    )
    return {'records': records}


# 艾宾浩斯复习间隔（天数）：第1次3天，第2次7天，第3次14天，第4次30天
def _get_next_review_interval(review_count: int) -> int:
    intervals = [3, 7, 14, 30]
    idx = min(review_count, len(intervals) - 1)
    return intervals[idx]


@router.post('/{record_id}/review')
def review_mistake(
    record_id: int,
    can_resolve: bool,
    confidence_level: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交错题复习结果
    - can_resolve: 孩子认为自己是否能做对
    - confidence_level: 1-5 信心等级
    如果 can_resolve=True 且 confidence_level >= 4，标记为已掌握；否则按艾宾浩斯曲线安排下次复习
    """
    record = db.query(MistakeRecord).filter(
        MistakeRecord.pk_mistake_records == record_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')
    if record.fk_users != current_user.pk_users:
        owner = db.query(User).filter(User.pk_users == record.fk_users).first()
        if not owner or owner.fk_users_parent != current_user.pk_users:
            raise HTTPException(status_code=403, detail='无权操作')

    now = datetime.now()
    review_count = record.review_count + 1

    # 判断是否已掌握
    if can_resolve and (confidence_level is None or confidence_level >= 4):
        record.resolved = True
        next_review_at = now + timedelta(days=30)  # 已掌握，30天后最终确认
    else:
        # 按艾宾浩斯曲线安排下次复习
        interval_days = _get_next_review_interval(review_count)
        next_review_at = now + timedelta(days=interval_days)

    record.review_count = review_count
    record.next_review_at = next_review_at

    # 创建复习记录
    review = MistakeReview(
        fk_mistake_records=record_id,
        can_resolve_now=can_resolve,
        confidence_level=confidence_level,
        reviewed_at=now,
        next_review_at=next_review_at,
    )
    db.add(review)
    db.commit()
    db.refresh(record)
    return {'record': record, 'review': {'can_resolve_now': can_resolve, 'confidence_level': confidence_level, 'next_review_at': next_review_at.isoformat(), 'resolved': record.resolved}}


@router.get('/analysis')
def get_analysis(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    records = (
        db.query(MistakeRecord)
        .filter(MistakeRecord.fk_users == target.pk_users)
        .all()
    )
    from collections import Counter
    categories = Counter(r.category for r in records if r.category)
    weak_points = Counter(r.knowledge_point for r in records if r.knowledge_point)
    return {
        'categoryDistribution': [{'category': k, 'count': v} for k, v in categories.most_common()],
        'weakPoints': [{'knowledgePoint': k, 'count': v} for k, v in weak_points.most_common(5)],
    }
