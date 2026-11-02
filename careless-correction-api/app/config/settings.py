import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings

# 历史遗留/示例密钥：命中这些值时一律视为「未配置」，
# 自动替换为随机密钥，避免公开仓库里的固定字符串被用来伪造 token。
_INSECURE_SECRETS = {
    '',
    'dev-secret-change-in-production',
    'please-change-me-to-a-long-random-secret',
    'change-me',
    'secret',
}


def _data_dir() -> Path:
    """与 SQLite 同目录（容器内是 /app/data，已挂载数据卷）。"""
    db_path = os.getenv('DB_PATH') or ''
    if db_path:
        return Path(db_path).expanduser().resolve().parent
    return Path(__file__).resolve().parent.parent.parent / 'data'


@lru_cache(maxsize=1)
def _load_or_create_jwt_secret() -> str:
    """读取持久化的 JWT 密钥；不存在则生成随机密钥写入数据目录。

    密钥落在数据卷内，容器重建/重启后 token 依然有效，无需人工配置；
    即使运维忘记设置 JWT_SECRET，也不会退化成「公开默认密钥」。
    """
    secret_file = _data_dir() / '.jwt_secret'
    try:
        if secret_file.exists():
            value = secret_file.read_text(encoding='utf-8').strip()
            if value and value not in _INSECURE_SECRETS:
                return value
        value = secrets.token_urlsafe(48)
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text(value, encoding='utf-8')
        try:
            os.chmod(secret_file, 0o600)
        except OSError:
            pass
        print(f'[security] 未配置 JWT_SECRET，已自动生成随机密钥：{secret_file}')
        return value
    except OSError as exc:  # 只读文件系统兜底：进程内随机，重启后需重新登录
        print(f'[security] 无法持久化 JWT 密钥（{exc}），本次使用临时密钥')
        return secrets.token_urlsafe(48)


class Settings(BaseSettings):
    jwt_secret: str = ''
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 525600  # 365 天（家庭 Pad 私有应用，物理安全可控，长 token 提升体验）
    # token 使用超过该时长后触发滑动续期（默认有效期一半）：活跃用户几乎永不掉线
    jwt_refresh_after_minutes: int = 262800
    upload_dir: str = './uploads'
    max_upload_mb: int = 8
    llm_endpoint: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = 'gpt-4o-mini'
    # 是否允许把 LLM endpoint 指向内网/回环地址（自建局域网大模型时才打开）
    llm_allow_private_endpoint: bool = False
    port: int = 3001

    # ===== CORS =====
    # 逗号分隔的白名单；留空表示不启用 CORS（同源部署无需 CORS）
    cors_origins: str = 'http://localhost,http://127.0.0.1,capacitor://localhost'
    # 显式允许任意来源（仅调试用，开启后不携带 credentials）
    cors_allow_all: bool = False

    # ===== 接口文档：默认关闭，避免把完整 API 结构暴露给无关访问者 =====
    enable_api_docs: bool = False

    # ===== 注册策略 =====
    # 首个家长账号可自由注册；已有家长账号后，注册必须携带该邀请码（为空则直接禁止新注册）
    register_invite_code: str = ''

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'extra': 'ignore'}

    @model_validator(mode='after')
    def _ensure_jwt_secret(self):
        if not self.jwt_secret or self.jwt_secret.strip() in _INSECURE_SECRETS:
            self.jwt_secret = _load_or_create_jwt_secret()
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(',') if o.strip()]
