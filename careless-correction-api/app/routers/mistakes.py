from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import MistakeRecord, User

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
