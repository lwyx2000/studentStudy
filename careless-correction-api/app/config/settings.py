from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = 'dev-secret-change-in-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 525600  # 365 天（家庭 Pad 私有应用，物理安全可控，长 token 提升体验）
    # token 使用超过该时长后触发滑动续期（默认有效期一半）：活跃用户几乎永不掉线
    jwt_refresh_after_minutes: int = 262800
    upload_dir: str = './uploads'
    llm_endpoint: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = 'gpt-4o-mini'
    port: int = 3001

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'extra': 'ignore'}
