from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import Settings
from app.database import get_db
from app.models import Assessment, User
from app.schemas import TokenOut, UserOut

router = APIRouter()
settings = Settings()

MIN_PASSWORD_LENGTH = 8


def _validate_password(password: str) -> None:
    """家长/孩子密码强度校验：长度 + 不能纯数字或纯字母。"""
    if len(password or '') < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f'密码至少 {MIN_PASSWORD_LENGTH} 位')
    if len(password) > 128:
        raise HTTPException(status_code=400, detail='密码过长')
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=400, detail='密码需同时包含字母和数字')


@router.post('/register', response_model=TokenOut, status_code=201)
def register(
    name: str,
    password: str,
    invite_code: str | None = None,
    db: Session = Depends(get_db),
):
    """注册家长账号。

    首个家长可自由注册；一旦已存在家长账号，必须提供 REGISTER_INVITE_CODE，
    未配置邀请码时直接禁止新增（家庭私有应用，避免任意人注册后看到家庭数据）。
    """
    name = (name or '').strip()
    if not 2 <= len(name) <= 30:
        raise HTTPException(status_code=400, detail='用户名长度需为 2-30 个字符')
    _validate_password(password)

    existing = db.query(User).filter(User.name == name, User.role == 'parent').first()
    if existing:
        raise HTTPException(status_code=409, detail='用户名已存在')

    has_parent = db.query(User).filter(User.role == 'parent').first() is not None
    if has_parent:
        expected = (settings.register_invite_code or '').strip()
        if not expected or (invite_code or '').strip() != expected:
            raise HTTPException(status_code=403, detail='已存在家长账号，注册需要正确的邀请码')

    user = User(name=name, role='parent', password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.pk_users, user.role)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.post('/login', response_model=TokenOut)
def login(
    name: str,
    password: str,
    db: Session = Depends(get_db),
):
    """登录（家长用name，孩子用login_name）"""
    user = (
        db.query(User).filter(User.name == name, User.role == 'parent').first()
        or db.query(User).filter(User.login_name == name, User.role == 'child').first()
    )
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    token = create_access_token(user.pk_users, user.role)
    return TokenOut(token=token, user=UserOut.model_validate(user))


@router.get('/session', response_model=UserOut)
def get_session(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post('/assessment')
def save_assessment(
    focus_attention: int,
    organization: int,
    emotional_control: int,
    planning: int,
    impulse_control: int,
    recommended_level: int,
    task_density: str = 'medium',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存注册评估结果并标记为已完成 onboarding"""
    assessment = Assessment(
        fk_users=current_user.pk_users,
        focus_attention=focus_attention,
        organization=organization,
        emotional_control=emotional_control,
        planning=planning,
        impulse_control=impulse_control,
        recommended_level=recommended_level,
        task_density=task_density,
        source='initial',
    )
    db.add(assessment)
    current_user.is_onboarded = True
    db.commit()
    return {'success': True, 'is_onboarded': True}


@router.put('/password')
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码（家长和孩子均可使用）"""
    if not current_user.password_hash or not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail='原密码错误')
    _validate_password(new_password)
    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {'success': True}


@router.put('/profile', response_model=UserOut)
def update_profile(
    name: str | None = None,
    grade: int | None = None,
    avatar_url: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if name is not None:
        name = name.strip()
        if not 1 <= len(name) <= 30:
            raise HTTPException(status_code=400, detail='昵称长度需为 1-30 个字符')
        current_user.name = name
    if grade is not None:
        if not 0 <= grade <= 12:
            raise HTTPException(status_code=400, detail='年级取值无效')
        current_user.grade = grade
    if avatar_url is not None:
        current_user.avatar_url = avatar_url[:255]
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
