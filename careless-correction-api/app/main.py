import os
import sys
from contextlib import asynccontextmanager

# 允许直接执行 python app/main.py：将项目根目录加入模块搜索路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request
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


def _normalize_checkin_dates(conn) -> int:
    """把历史打卡日期统一成 YYYY-MM-DD。

    早期版本允许 `2026/8/1` 这类写法，导致同一天分裂成多条记录、连续天数算错，
    也让按日期的等值查询失效（只能把整表读进内存逐条解析）。这里一次性归一。
    """
    rows = conn.execute(text('SELECT pk_check_ins, check_date FROM t_check_ins')).fetchall()
    fixed = 0
    for pk, raw in rows:
        if not raw:
            continue
        s = str(raw).strip().replace('/', '-').replace('.', '-')
        parts = s.split('-')
        if len(parts) != 3:
            continue
        try:
            iso = f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
        except ValueError:
            continue
        if iso != raw:
            conn.execute(
                text('UPDATE t_check_ins SET check_date = :iso WHERE pk_check_ins = :pk'),
                {'iso': iso, 'pk': pk},
            )
            fixed += 1
    return fixed


# 高频查询路径的索引：不建索引时每个接口都要全表扫描，数据量涨起来后
# 打卡页（每次提交要读 3~4 次打卡表）会明显变慢。
_INDEXES = (
    ('ix_check_ins_user_date', 'CREATE INDEX IF NOT EXISTS ix_check_ins_user_date ON t_check_ins(fk_users, check_date)'),
    ('ix_check_ins_user_status', 'CREATE INDEX IF NOT EXISTS ix_check_ins_user_status ON t_check_ins(fk_users, status)'),
    ('ix_tasks_user_active', 'CREATE INDEX IF NOT EXISTS ix_tasks_user_active ON t_tasks(fk_users, active)'),
    ('ix_tasks_user_assigned', 'CREATE INDEX IF NOT EXISTS ix_tasks_user_assigned ON t_tasks(fk_users, assigned_date)'),
    ('ix_sub_tasks_task', 'CREATE INDEX IF NOT EXISTS ix_sub_tasks_task ON t_sub_tasks(fk_tasks)'),
    ('ix_habit_sops_user', 'CREATE INDEX IF NOT EXISTS ix_habit_sops_user ON t_habit_sops(fk_users, active)'),
    ('ix_sop_steps_habit', 'CREATE INDEX IF NOT EXISTS ix_sop_steps_habit ON t_sop_steps(fk_habit_sops)'),
    ('ix_sunlight_user_time', 'CREATE INDEX IF NOT EXISTS ix_sunlight_user_time ON t_sunlight_history(fk_users, created_at)'),
    ('ix_apple_user_time', 'CREATE INDEX IF NOT EXISTS ix_apple_user_time ON t_apple_history(fk_users, created_at)'),
    ('ix_apple_req_user_status', 'CREATE INDEX IF NOT EXISTS ix_apple_req_user_status ON t_apple_redemption_requests(fk_users, status)'),
    ('ix_pending_user_collected', 'CREATE INDEX IF NOT EXISTS ix_pending_user_collected ON t_pending_sunlight(fk_users, collected)'),
    ('ix_mistakes_user_due', 'CREATE INDEX IF NOT EXISTS ix_mistakes_user_due ON t_mistake_records(fk_users, next_review_at)'),
    ('ix_mistake_reviews_record', 'CREATE INDEX IF NOT EXISTS ix_mistake_reviews_record ON t_mistake_reviews(fk_mistake_records)'),
    ('ix_badge_unlocks_user', 'CREATE INDEX IF NOT EXISTS ix_badge_unlocks_user ON t_badge_unlocks(fk_users)'),
    ('ix_growth_user_date', 'CREATE INDEX IF NOT EXISTS ix_growth_user_date ON t_growth_snapshots(fk_users, snapshot_date)'),
    ('ix_alerts_user_time', 'CREATE INDEX IF NOT EXISTS ix_alerts_user_time ON t_diagnostic_alerts(fk_users, created_at)'),
    ('ix_item_loss_user', 'CREATE INDEX IF NOT EXISTS ix_item_loss_user ON t_item_loss_records(fk_users)'),
    ('ix_item_storage_user', 'CREATE INDEX IF NOT EXISTS ix_item_storage_user ON t_item_storage_records(fk_users)'),
    ('ix_reward_items_user', 'CREATE INDEX IF NOT EXISTS ix_reward_items_user ON t_reward_items(fk_users)'),
    ('ix_weekly_progress_user', 'CREATE INDEX IF NOT EXISTS ix_weekly_progress_user ON t_task_weekly_progress(fk_users)'),
)


def _create_indexes():
    """在 create_all 之后执行：新库也要有索引。

    单个索引失败（例如老库缺列）只打印告警，不影响启动——绝不能因为建索引
    失败导致整个服务起不来。
    """
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    created = 0
    with engine.connect() as conn:
        for _name, ddl in _INDEXES:
            table = ddl.split(' ON ')[1].split('(')[0].strip()
            if table not in tables:
                continue
            try:
                conn.execute(text(ddl))
                created += 1
            except Exception as exc:  # noqa: BLE001 - 任何失败都不应阻断启动
                print(f'[migrate] 创建索引失败（{table}）：{exc}')
        conn.commit()
    return created


def _run_migrations():
    """Run schema migrations for existing databases."""
    with engine.connect() as conn:
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        if 't_users' in tables:
            columns = [c['name'] for c in insp.get_columns('t_users')]
            if 'apples' not in columns:
                conn.execute(text('ALTER TABLE t_users ADD COLUMN apples INTEGER NOT NULL DEFAULT 0'))
        # 子任务可选标记（加分项）
        if 't_sub_tasks' in tables:
            columns = [c['name'] for c in insp.get_columns('t_sub_tasks')]
            if 'is_optional' not in columns:
                conn.execute(text('ALTER TABLE t_sub_tasks ADD COLUMN is_optional BOOLEAN NOT NULL DEFAULT 0'))
            if 'reward_points' not in columns:
                conn.execute(text('ALTER TABLE t_sub_tasks ADD COLUMN reward_points SMALLINT NULL'))
        # 打卡阳光值构成明细
        if 't_check_ins' in tables:
            columns = [c['name'] for c in insp.get_columns('t_check_ins')]
            if 'required_points' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN required_points INTEGER NOT NULL DEFAULT 0'))
            if 'optional_bonus' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN optional_bonus INTEGER NOT NULL DEFAULT 0'))
            if 'all_done_bonus' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN all_done_bonus INTEGER NOT NULL DEFAULT 0'))
            if 'habit_points' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN habit_points INTEGER NOT NULL DEFAULT 0'))
            if 'reject_reason' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN reject_reason TEXT NULL'))
            if 'completed_tasks_snapshot' not in columns:
                conn.execute(text('ALTER TABLE t_check_ins ADD COLUMN completed_tasks_snapshot TEXT NULL'))

        # 一条打卡最多对应一条「待收集阳光」：并发审批曾可能生成多条，导致重复发放。
        # SQLite 的 UNIQUE 索引允许多个 NULL，因此不影响家长手动发放（fk_check_ins 为空）。
        if 't_pending_sunlight' in tables:
            rows = conn.execute(text(
                'SELECT pk_pending_sunlight, fk_check_ins, collected FROM t_pending_sunlight '
                'WHERE fk_check_ins IS NOT NULL '
                'ORDER BY fk_check_ins, collected DESC, pk_pending_sunlight DESC'
            )).fetchall()
            seen: set[int] = set()
            dup_ids: list[int] = []
            for pk, checkin_id, _collected in rows:
                if checkin_id in seen:
                    dup_ids.append(pk)
                else:
                    seen.add(checkin_id)
            for pk in dup_ids:
                conn.execute(
                    text('DELETE FROM t_pending_sunlight WHERE pk_pending_sunlight = :pk'),
                    {'pk': pk},
                )
            conn.execute(text(
                'CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_sunlight_checkin '
                'ON t_pending_sunlight(fk_check_ins)'
            ))
        if 't_check_ins' in tables:
            fixed = _normalize_checkin_dates(conn)
            if fixed:
                print(f'[migrate] 归一化打卡日期 {fixed} 条')
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
    Base.metadata.create_all(bind=engine)
    _create_indexes()
    # 初始化基础数据（勋章定义、循证文章），仅在表为空时插入
    from app.services.seed import seed_initial_data
    with SessionLocal() as db:
        badges_count, articles_count = seed_initial_data(db)
        if badges_count or articles_count:
            print(f'[seed] 初始化勋章 {badges_count} 个、文章 {articles_count} 篇')
    yield


_docs_enabled = bool(settings.enable_api_docs)
app = FastAPI(
    title='小树成长岛 API',
    version='1.0.0',
    lifespan=lifespan,
    # 文档默认关闭：完整 API 结构无需对无关访问者公开
    docs_url='/docs' if _docs_enabled else None,
    redoc_url='/redoc' if _docs_enabled else None,
    openapi_url='/openapi.json' if _docs_enabled else None,
)


@app.get('/health')
async def health():
    """健康检查端点（供 Docker HEALTHCHECK / nginx 探活使用）"""
    return {'status': 'ok', 'service': 'studentstudy-api'}


# CORS 收敛为白名单：默认只允许本地/容器的 WebView 来源。
# 鉴权走 Authorization 头而非 Cookie，因此不开启 allow_credentials。
_cors_origins = settings.cors_origin_list
if settings.cors_allow_all or _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'] if settings.cors_allow_all else _cors_origins,
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['X-Refreshed-Token'],
    )


@app.middleware('http')
async def refresh_token_middleware(request: Request, call_next):
    """若本请求的鉴权触发了滑动续期，把新 token 放入响应头供前端保存。"""
    response = await call_next(request)
    new_token = getattr(request.state, 'refreshed_token', None)
    if new_token:
        response.headers['X-Refreshed-Token'] = new_token
    return response


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
