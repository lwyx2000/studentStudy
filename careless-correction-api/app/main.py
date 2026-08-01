import os
import sys
from contextlib import asynccontextmanager

# 允许直接执行 python app/main.py：将项目根目录加入模块搜索路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.config import Settings

from app.database import Base, engine, SessionLocal
from app.routers import (
    articles, auth, badges, checkins, children, growth, habits,
    items, llm, mistakes, parent, points, tasks,
)

settings = Settings()


def _run_migrations():
    """Run schema migrations for existing databases."""
    with engine.connect() as conn:
        insp = inspect(engine)
        if 't_users' in insp.get_table_names():
            columns = [c['name'] for c in insp.get_columns('t_users')]
            if 'apples' not in columns:
                conn.execute(text('ALTER TABLE t_users ADD COLUMN apples INTEGER NOT NULL DEFAULT 0'))
        # 清理已删除功能的历史表（社区/契约）——先删子表再删父表，避免外键约束
        existing = set(insp.get_table_names())
        for table in ('t_covenant_signatures', 't_shared_covenants', 't_post_replies',
                      't_covenants', 't_community_posts'):
            if table in existing:
                conn.execute(text(f'DROP TABLE IF EXISTS {table}'))
        conn.commit()
    # t_apple_history will be created by create_all below


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
    Base.metadata.create_all(bind=engine)
    # 初始化基础数据（勋章定义、循证文章），仅在表为空时插入
    from app.services.seed import seed_initial_data
    with SessionLocal() as db:
        badges_count, articles_count = seed_initial_data(db)
        if badges_count or articles_count:
            print(f'[seed] 初始化勋章 {badges_count} 个、文章 {articles_count} 篇')
    yield


app = FastAPI(title='小树成长岛 API', version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.mount('/uploads', StaticFiles(directory=settings.upload_dir), name='uploads')

app.include_router(auth.router, prefix='/api/v1/auth', tags=['认证'])
app.include_router(children.router, prefix='/api/v1/children', tags=['孩子管理'])
app.include_router(tasks.router, prefix='/api/v1/tasks', tags=['任务'])
app.include_router(habits.router, prefix='/api/v1/habits', tags=['习惯 SOP'])
app.include_router(mistakes.router, prefix='/api/v1/mistakes', tags=['错题'])
app.include_router(items.router, prefix='/api/v1/items', tags=['物品'])
app.include_router(points.router, prefix='/api/v1/points', tags=['阳光值'])
app.include_router(badges.router, prefix='/api/v1/badges', tags=['勋章'])
app.include_router(checkins.router, prefix='/api/v1/checkins', tags=['打卡审批'])
app.include_router(growth.router, prefix='/api/v1/growth', tags=['成长'])
app.include_router(llm.router, prefix='/api/v1/llm', tags=['LLM 配置'])
app.include_router(parent.router, prefix='/api/v1/parent', tags=['家长设置'])
app.include_router(articles.router, prefix='/api/v1/articles', tags=['文章资源'])


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=settings.port, reload=True)
