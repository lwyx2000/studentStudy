import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.database import db_config

# 确保 SQLite 数据库目录存在
os.makedirs(os.path.dirname(db_config.db_path), exist_ok=True)

engine = create_engine(
    db_config.url,
    echo=False,
    connect_args={'check_same_thread': False},
)


# 启用 SQLite 外键约束
@event.listens_for(engine, 'connect')
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
