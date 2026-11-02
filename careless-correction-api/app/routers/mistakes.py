from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import Settings
from app.database import get_db
from app.models import MistakeRecord, MistakeReview, User

router = APIRouter()
settings = Settings()


def _detect_image_ext(content: bytes) -> str | None:
    """按文件头判断图片类型，不信任客户端声明的 Content-Type / 扩展名。"""
    if content.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if content.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return '.webp'
    if content[:6] in (b'GIF87a', b'GIF89a'):
        return '.gif'
    return None


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

    max_bytes = max(1, settings.max_upload_mb) * 1024 * 1024
    # 分块上限读取：超过上限立即拒绝，避免大文件整块进内存
    content = await image.read(max_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail='上传文件为空')
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f'图片不能超过 {settings.max_upload_mb} MB')

    ext = _detect_image_ext(content)
    if not ext:
        raise HTTPException(status_code=400, detail='仅支持 JPG / PNG / WEBP / GIF 图片')

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    # 文件名完全由服务端生成（随机），不含用户输入：既防路径穿越，也避免被枚举
    file_name = f'mistake_{uuid.uuid4().hex}{ext}'
    (upload_dir / file_name).write_bytes(content)
    return {'imageUrl': f'/uploads/{file_name}'}


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


# 艾宾浩斯复习间隔（天数）：第1次复习后 3 天，第2次 7 天，第3次 14 天，第4次及以后 30 天
def _get_next_review_interval(review_count: int) -> int:
    intervals = [3, 7, 14, 30]
    # review_count 是「本次是第几次复习」（从 1 开始），所以要减 1 取下标；
    # 旧实现直接用 review_count 当索引，第一次复习就排到了 7 天后。
    idx = min(max(review_count - 1, 0), len(intervals) - 1)
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
