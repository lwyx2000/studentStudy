from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import LlmConfig, User
from app.services.llm import call_llm

router = APIRouter()


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
            'apiKey': '***' if config.api_key else '',
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
