from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import LlmConfig, User
from app.services.llm import call_llm

router = APIRouter()

# 读取配置时用占位符代替真实 Key，避免明文回传；保存时收到占位符代表「未修改」
API_KEY_PLACEHOLDER = '***'


def _clean_endpoint(endpoint: str | None) -> str | None:
    """保存前做基础格式校验，避免存入明显不可用的地址。"""
    if endpoint is None:
        return None
    ep = endpoint.strip()
    if not ep:
        return ''
    parsed = urlparse(ep)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise HTTPException(status_code=400, detail='endpoint 必须是 http(s):// 开头的完整地址')
    if len(ep) > 255:
        raise HTTPException(status_code=400, detail='endpoint 过长')
    return ep.rstrip('/')


def _clean_api_key(api_key: str | None) -> str | None:
    """前端拿到的是占位符，原样回传时必须忽略，否则真实 Key 会被 `***` 覆盖。"""
    if api_key is None:
        return None
    key = api_key.strip()
    if not key or key == API_KEY_PLACEHOLDER:
        return None
    if len(key) > 255:
        raise HTTPException(status_code=400, detail='API Key 过长')
    return key


@router.get('/config')
def get_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(LlmConfig).filter(LlmConfig.fk_users == current_user.pk_users).first()
    if not config:
        return {'config': None}
    return {
        'config': {
            'pk_llm_config': config.pk_llm_config,
            'endpoint': config.endpoint,
            'model': config.model,
            'mistake_prompt': config.mistake_prompt,
            'assessment_prompt': config.assessment_prompt,
            'assessment_cron': config.assessment_cron,
            'enabled': config.enabled,
            'apiKey': API_KEY_PLACEHOLDER if config.api_key else '',
        }
    }


@router.put('/config')
def update_config(
    endpoint: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    mistake_prompt: str | None = None,
    assessment_prompt: str | None = None,
    assessment_cron: str | None = None,
    enabled: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(LlmConfig).filter(LlmConfig.fk_users == current_user.pk_users).first()
    endpoint = _clean_endpoint(endpoint)
    api_key = _clean_api_key(api_key)
    if config:
        if endpoint is not None:
            config.endpoint = endpoint
        if api_key is not None:
            config.api_key = api_key
        if model is not None:
            config.model = model
        if mistake_prompt is not None:
            config.mistake_prompt = mistake_prompt
        if assessment_prompt is not None:
            config.assessment_prompt = assessment_prompt
        if assessment_cron is not None:
            config.assessment_cron = assessment_cron
        if enabled is not None:
            config.enabled = enabled
    else:
        config = LlmConfig(
            fk_users=current_user.pk_users,
            endpoint=endpoint or '',
            api_key=api_key or '',
            model=model or '',
            mistake_prompt=mistake_prompt or '',
            assessment_prompt=assessment_prompt or '',
            assessment_cron=assessment_cron or 'weekly',
            enabled=enabled or False,
        )
        db.add(config)
    db.commit()
    return {'success': True}


@router.post('/test')
async def test_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(LlmConfig).filter(LlmConfig.fk_users == current_user.pk_users).first()
    if not config:
        raise HTTPException(status_code=400, detail='请先保存配置')
    try:
        result = await call_llm(config, '回复"连接成功"')
        return {'success': True, 'result': result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'连接失败：{str(e)}')
