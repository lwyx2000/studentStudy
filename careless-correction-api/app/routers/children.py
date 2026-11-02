import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from pypinyin import lazy_pinyin
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, require_parent
from app.database import get_db
from app.models import (
    AppleHistory, AppleRedemptionRequest, ArticleBookmark, Assessment, BadgeUnlock,
    CheckIn, DiagnosticAlert, GrowthReport, GrowthSnapshot, HabitSOP, ItemLossRecord,
    ItemStorageRecord, LlmConfig, MistakeRecord, MistakeReview, ParentSetting,
    PendingSunlight, RewardItem, SOPStep, SubTask, SunlightHistory, Task,
    TaskWeeklyProgress, User,
)
from app.schemas import ChildOut, TokenOut


def _generate_child_password(length: int = 10) -> str:
    """生成随机初始密码：字母 + 数字，满足密码强度校验。"""
    alphabet = string.ascii_lowercase + string.digits
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isalpha() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


def _make_login_name(name: str) -> str:
    return ''.join([word[0].lower() for word in lazy_pinyin(name)])


def _generate_unique_login_name(name: str, db: Session) -> str:
    base = _make_login_name(name)
    existing = db.query(User.login_name).filter(
        User.login_name.like(f'{base}%')
    ).all()
    used = {row[0] for row in existing if row[0]}
    if base not in used:
        return base
    suffix = 1
    while f'{base}{suffix}' in used:
        suffix += 1
    return f'{base}{suffix}'


def _purge_owned_rows(db: Session, user_id: int) -> None:
    """按外键依赖顺序清理该用户名下所有业务数据。

    这些外键都是 NOT NULL 且未设置级联删除，直接 DELETE 用户会被 SQLAlchemy
    改成「把子表外键置 NULL」，触发 NOT NULL 约束错误（500）。必须显式按序删除。
    """
    task_ids = db.query(Task.pk_tasks).filter(Task.fk_users == user_id)
    mistake_ids = db.query(MistakeRecord.pk_mistake_records).filter(MistakeRecord.fk_users == user_id)
    habit_ids = db.query(HabitSOP.pk_habit_sops).filter(HabitSOP.fk_users == user_id)

    # 1) 引用打卡记录的待收集阳光
    db.query(PendingSunlight).filter(PendingSunlight.fk_users == user_id).delete(synchronize_session=False)
    # 2) 错题 → 复习记录
    db.query(MistakeReview).filter(MistakeReview.fk_mistake_records.in_(mistake_ids)).delete(synchronize_session=False)
    # 3) 任务 → 子任务（Task 引用 HabitSOP，必须早于习惯删除）
    db.query(SubTask).filter(SubTask.fk_tasks.in_(task_ids)).delete(synchronize_session=False)
    db.query(Task).filter(Task.fk_users == user_id).delete(synchronize_session=False)
    # 4) 习惯步骤 → 习惯
    db.query(SOPStep).filter(SOPStep.fk_habit_sops.in_(habit_ids)).delete(synchronize_session=False)
    db.query(HabitSOP).filter(HabitSOP.fk_users == user_id).delete(synchronize_session=False)
    # 5) 其余直接挂在用户下的表
    for model in (
        CheckIn, MistakeRecord, ItemStorageRecord, ItemLossRecord, RewardItem,
        SunlightHistory, AppleHistory, AppleRedemptionRequest, GrowthSnapshot,
        DiagnosticAlert, GrowthReport, TaskWeeklyProgress, Assessment,
        LlmConfig, ParentSetting, ArticleBookmark, BadgeUnlock,
    ):
        db.query(model).filter(model.fk_users == user_id).delete(synchronize_session=False)


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


@router.post('/', status_code=201)
def add_child(
    name: str,
    grade: int = 3,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """家长添加孩子账号。

    初始密码随机生成并只在本次响应返回（家长需转告孩子），
    避免所有孩子共用同一个公开默认密码。
    """
    existing = db.query(User).filter(
        User.name == name,
        User.fk_users_parent == current_user.pk_users,
        User.role == 'child',
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail='已存在同名孩子')
    initial_password = _generate_child_password()
    child = User(
        name=name,
        login_name=_generate_unique_login_name(name, db),
        role='child',
        password_hash=hash_password(initial_password),
        grade=grade,
        fk_users_parent=current_user.pk_users,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return {
        **ChildOut.model_validate(child).model_dump(),
        'initialPassword': initial_password,
    }


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
    _purge_owned_rows(db, child.pk_users)
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
