import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """数据库配置，使用本地 SQLite"""

    db_path: str = ''

    def __init__(self):
        # 默认在项目根目录下生成 data/app.db
        default_path = str(Path(__file__).resolve().parent.parent.parent / 'data' / 'app.db')
        self.db_path = os.getenv('DB_PATH', default_path)

    @property
    def url(self) -> str:
        return f'sqlite:///{self.db_path}'


db_config = DatabaseConfig()
