import os
from urllib.parse import quote_plus


class DatabaseConfig:
    """数据库配置，优先从环境变量读取，使用默认值兜底"""

    host: str = 'localhost'
    port: int = 3306
    user: str = 'root'
    password: str = ''
    database: str = 'careless_correction'

    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('DB_USER', 'root')
        raw_password = os.getenv('DB_PASSWORD', '')
        self.password = quote_plus(raw_password) if raw_password else ''
        self.database = os.getenv('DB_NAME', 'careless_correction')

    @property
    def url(self) -> str:
        return f'mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4'


db_config = DatabaseConfig()
