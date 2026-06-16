from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = 'dev-secret-change-in-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 1440
    upload_dir: str = './uploads'
    llm_endpoint: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = 'gpt-4o-mini'
    port: int = 3001

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'extra': 'ignore'}
