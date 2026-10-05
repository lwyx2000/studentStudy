"""登录滑动续期（长期有效）行为测试。

背景：家庭 Pad 私有应用，登录一次应长期有效——token 有效期 365 天，
使用超过续期阈值（默认 180 天）后由任意请求顺带换发新 token，
前端从 X-Refreshed-Token 响应头自动替换本地存储。
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session as SASession

from app.auth import create_access_token
from app.config import Settings
from app.database import Base, engine
from app.main import app
from app.models import User

settings = Settings()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

PARENT_NAME = 'refresh_parent'
PARENT_PASSWORD = 'pw123456'
_parent_pk: int | None = None


@pytest.fixture(scope='module', autouse=True)
def _prepare_db():
    """建表并创建测试家长账号；结束后清理，保证重复运行幂等。"""
    global _parent_pk
    Base.metadata.create_all(bind=engine)
    with SASession(engine) as s:
        user = User(
            name=PARENT_NAME, role='parent',
            password_hash=pwd_context.hash(PARENT_PASSWORD), grade=0, is_onboarded=True,
        )
        s.add(user)
        s.commit()
        _parent_pk = user.pk_users
    yield
    with SASession(engine) as s:
        s.query(User).filter(User.name == PARENT_NAME).delete()
        s.commit()


@pytest.fixture()
def client():
    return TestClient(app)


def _headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _make_token(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_login_returns_token_without_refresh(client):
    r = client.post('/api/v1/auth/login', params={'name': PARENT_NAME, 'password': PARENT_PASSWORD})
    assert r.status_code == 200
    token = r.json()['token']
    assert 'X-Refreshed-Token' not in r.headers

    r = client.get('/api/v1/auth/session', headers=_headers(token))
    assert r.status_code == 200
    assert 'X-Refreshed-Token' not in r.headers


def test_legacy_token_without_iat_refreshes_once(client):
    """旧版本签发的 token（无 iat）：首次请求即换发，完成平滑迁移。"""
    legacy = _make_token({
        'pk_users': _parent_pk, 'role': 'parent',
        'exp': datetime.now(timezone.utc) + timedelta(days=90),
    })
    r = client.get('/api/v1/auth/session', headers=_headers(legacy))
    assert r.status_code == 200
    refreshed = r.headers.get('X-Refreshed-Token')
    assert refreshed, '旧格式 token 应触发续期'
    # 换发后的新 token 立即可用
    r2 = client.get('/api/v1/auth/session', headers=_headers(refreshed))
    assert r2.status_code == 200
    assert 'X-Refreshed-Token' not in r2.headers


def test_refresh_only_after_threshold(client):
    """阈值内（180 天内用过）不续期，避免每个请求都换发。"""
    now = datetime.now(timezone.utc)
    recent = _make_token({
        'pk_users': _parent_pk, 'role': 'parent',
        'iat': now - timedelta(minutes=settings.jwt_refresh_after_minutes - 10),
        'exp': now + timedelta(days=30),
    })
    r = client.get('/api/v1/auth/session', headers=_headers(recent))
    assert r.status_code == 200
    assert 'X-Refreshed-Token' not in r.headers


def test_aged_token_refreshes_and_resets_full_window(client):
    """超过阈值的 token 触发续期，新 token 有效期从当下重新计算。"""
    now = datetime.now(timezone.utc)
    aged = _make_token({
        'pk_users': _parent_pk, 'role': 'parent',
        'iat': now - timedelta(minutes=settings.jwt_refresh_after_minutes + 10),
        'exp': now + timedelta(days=1),
    })
    r = client.get('/api/v1/auth/session', headers=_headers(aged))
    assert r.status_code == 200
    refreshed = r.headers.get('X-Refreshed-Token')
    assert refreshed, '超阈值 token 应触发续期'

    payload = jwt.decode(refreshed, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload['pk_users'] == _parent_pk
    # 新 token 的完整有效期 = jwt_expire_minutes，且从现在起算
    assert payload['exp'] - payload['iat'] == settings.jwt_expire_minutes * 60
    remaining = payload['exp'] - now.timestamp()
    assert remaining > settings.jwt_expire_minutes * 60 * 0.99


def test_expired_token_still_rejected(client):
    expired = _make_token({
        'pk_users': _parent_pk, 'role': 'parent',
        'exp': datetime.now(timezone.utc) - timedelta(seconds=1),
    })
    r = client.get('/api/v1/auth/session', headers=_headers(expired))
    assert r.status_code == 401


def test_invalid_secret_token_rejected(client):
    forged = jwt.encode(
        {'pk_users': _parent_pk, 'role': 'parent', 'exp': datetime.now(timezone.utc) + timedelta(days=1)},
        'wrong-secret', algorithm=settings.jwt_algorithm,
    )
    r = client.get('/api/v1/auth/session', headers=_headers(forged))
    assert r.status_code == 401


def test_switch_token_includes_iat(client):
    """所有签发入口（登录/切换孩子）统一带 iat，均可参与后续续期。"""
    r = client.post('/api/v1/auth/login', params={'name': PARENT_NAME, 'password': PARENT_PASSWORD})
    payload = jwt.decode(r.json()['token'], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert 'iat' in payload
    assert payload['exp'] - payload['iat'] == settings.jwt_expire_minutes * 60
