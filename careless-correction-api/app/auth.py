from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.models import User

settings = Settings()
security = HTTPBearer()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'pk_users': user_id,
        'role': role,
        'iat': now,
        'exp': now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def should_refresh_token(token: str) -> bool:
    """token 已使用超过续期阈值（默认一半有效期）时返回 True，触发滑动续期。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return False
    iat = payload.get('iat')
    if not iat:
        return True  # 无签发时间的旧 token：直接视为需要续期
    age_seconds = datetime.now(timezone.utc).timestamp() - float(iat)
    return age_seconds >= settings.jwt_refresh_after_minutes * 60


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get('pk_users')
        if user_id is None:
            raise HTTPException(status_code=401, detail='无效的 token')
    except JWTError:
        raise HTTPException(status_code=401, detail='无效的 token')

    user = db.query(User).filter(User.pk_users == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail='用户不存在')

    # 滑动续期：token 用得越久越接近过期，达到阈值后本请求顺带签发新 token，
    # 由 main.py 的中间件放进响应头，前端自动替换本地存储，
    # 实现「只要还在使用就无需重新登录」。
    # 注意：这里用 request.state（基于共享的 ASGI scope）而不是 ContextVar——
    # 同步依赖在线程池里运行，ContextVar 的修改不会传播回请求上下文。
    if should_refresh_token(token):
        request.state.refreshed_token = create_access_token(user.pk_users, user.role)
    return user


def require_parent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='仅家长可操作')
    return current_user
