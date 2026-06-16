from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
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
    payload = {
        'pk_users': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
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
    return user


def require_parent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='仅家长可操作')
    return current_user
