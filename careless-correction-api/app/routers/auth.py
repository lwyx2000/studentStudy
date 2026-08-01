from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import Assessment, User
from app.schemas import ChildOut, TokenOut, UserOut

router = APIRouter()


@router.post('/register', response_model=TokenOut, status_code=201)
def register(
    name: str,
    password: str,
    db: Session = Depends(get_db),
):
    """注册家长账号"""
    existing = db.query(User).filter(User.name == name, User.role == 'parent').first()
    if existing:
        raise HTTPException(status_code=409, detail='用户名已存在')
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


@router.post('/child-login', response_model=TokenOut)
def child_login(
    child_id: int,
    parent_id: int,
    db: Session = Depends(get_db),
):
    """以孩子身份登录（家长端切换），无需密码，验证父子关系"""
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == parent_id,
        User.role == 'child',
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    token = create_access_token(child.pk_users, child.role)
    return TokenOut(token=token, user=UserOut.model_validate(child))


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
        current_user.name = name
    if grade is not None:
        current_user.grade = grade
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
