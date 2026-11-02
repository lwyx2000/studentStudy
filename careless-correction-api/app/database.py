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


# SQLite 连接级配置：
# - foreign_keys=ON：让外键约束生效，避免产生孤儿数据
# - journal_mode=WAL：读写并发不再互相阻塞（默认 rollback journal 下读会阻塞写）
# - busy_timeout=5000：写锁冲突时等待 5s 而不是立刻抛 "database is locked"
# - synchronous=NORMAL：WAL 下兼顾安全与性能
@event.listens_for(engine, 'connect')
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute('PRAGMA journal_mode=WAL')
    except Exception:  # 部分文件系统（网络盘）不支持 WAL，退回默认模式
        pass
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA busy_timeout=5000')
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
