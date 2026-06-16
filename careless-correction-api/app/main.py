from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.database import Base, engine
from app.routers import (
    auth, badges, children, community, covenants, growth, habits,
    items, llm, mistakes, parent, points, tasks,
)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
app.include_router(covenants.router, prefix='/api/v1/covenants', tags=['契约'])
app.include_router(growth.router, prefix='/api/v1/growth', tags=['成长'])
app.include_router(llm.router, prefix='/api/v1/llm', tags=['LLM 配置'])
app.include_router(parent.router, prefix='/api/v1/parent', tags=['家长设置'])
app.include_router(community.router, prefix='/api/v1/community', tags=['社区'])


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=settings.port, reload=True)
