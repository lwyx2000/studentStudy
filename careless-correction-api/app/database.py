from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.database import db_config

engine = create_engine(db_config.url, echo=False, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
