"""启动时初始化基础数据：勋章定义（按名称增量插入）、循证文章（仅在空表时插入）。"""
from datetime import datetime

from app.models import Article, Badge


def seed_badges(db) -> int:
    """插入勋章定义（增量：按 name 去重，仅插入缺失项）。"""
    existing_names = {name for (name,) in db.query(Badge.name).all()}

    badges = [
        Badge(
            name='初来乍到', description='完成第一次打卡，开始成长之旅',
            icon='🌱', color='#a5d6a7',
            requirement='完成 1 次打卡审批', requirement_type='checkin_count',
            requirement_value=1, reward_points=10,
        ),
        Badge(
            name='坚持一周', description='连续打卡 7 天',
            icon='🔥', color='#ffab91',
            requirement='连续打卡 7 天', requirement_type='streak_days',
            requirement_value=7, reward_points=30,
        ),
        Badge(
            name='月度之星', description='连续打卡 30 天',
            icon='⭐', color='#fff59d',
            requirement='连续打卡 30 天', requirement_type='streak_days',
            requirement_value=30, reward_points=100,
        ),
        Badge(
            name='任务达人', description='累计完成 30 个任务',
            icon='🎯', color='#90caf9',
            requirement='累计完成 30 个任务', requirement_type='task_complete',
            requirement_value=30, reward_points=30,
        ),
        Badge(
            name='任务大师', description='累计完成 100 个任务',
            icon='🏆', color='#ffe082',
            requirement='累计完成 100 个任务', requirement_type='task_complete',
            requirement_value=100, reward_points=80,
        ),
        Badge(
            name='错题侦探', description='累计记录 20 道错题',
            icon='🔍', color='#ce93d8',
            requirement='累计记录 20 道错题', requirement_type='mistake_count',
            requirement_value=20, reward_points=20,
        ),
        Badge(
            name='零丢失卫士', description='30 天没有物品丢失记录',
            icon='🛡️', color='#80cbc4',
            requirement='零丢失 30 天', requirement_type='zero_loss_days',
            requirement_value=30, reward_points=40,
        ),
        Badge(
            name='苹果种植家', description='种出 3 个苹果',
            icon='🍎', color='#ef9a9a',
            requirement='种出 3 个苹果', requirement_type='apple_count',
            requirement_value=3, reward_points=30,
        ),
        Badge(
            name='阳光富翁', description='累计获得 500 阳光值',
            icon='☀️', color='#ffcc80',
            requirement='累计获得 500 阳光值', requirement_type='sunlight_earned_total',
            requirement_value=500, reward_points=50,
        ),
        Badge(
            name='阳光收集家', description='累计获得 1000 阳光值',
            icon='💎', color='#f48fb1',
            requirement='累计获得 1000 阳光值', requirement_type='sunlight_earned_total',
            requirement_value=1000, reward_points=100,
        ),
        # ── 第二轮扩展勋章（10 个）──
        Badge(
            name='坚持三天', description='连续打卡 3 天',
            icon='📅', color='#b3e5fc',
            requirement='连续打卡 3 天', requirement_type='streak_days',
            requirement_value=3, reward_points=15,
        ),
        Badge(
            name='打卡小能手', description='累计通过 10 次打卡审批',
            icon='💯', color='#c5e1a5',
            requirement='累计通过 10 次打卡审批', requirement_type='checkin_count',
            requirement_value=10, reward_points=20,
        ),
        Badge(
            name='打卡大师', description='累计通过 50 次打卡审批',
            icon='🥇', color='#fff59d',
            requirement='累计通过 50 次打卡审批', requirement_type='checkin_count',
            requirement_value=50, reward_points=60,
        ),
        Badge(
            name='任务新秀', description='累计完成 10 个任务',
            icon='🌿', color='#b39ddb',
            requirement='累计完成 10 个任务', requirement_type='task_complete',
            requirement_value=10, reward_points=15,
        ),
        Badge(
            name='错题新手', description='累计记录 5 道错题',
            icon='🔎', color='#90caf9',
            requirement='累计记录 5 道错题', requirement_type='mistake_count',
            requirement_value=5, reward_points=10,
        ),
        Badge(
            name='收纳小能手', description='7 天没有物品丢失记录',
            icon='🧺', color='#80cbc4',
            requirement='零丢失 7 天', requirement_type='zero_loss_days',
            requirement_value=7, reward_points=20,
        ),
        Badge(
            name='苹果小农夫', description='种出 1 个苹果',
            icon='🌾', color='#ef9a9a',
            requirement='种出 1 个苹果', requirement_type='apple_count',
            requirement_value=1, reward_points=10,
        ),
        Badge(
            name='苹果大庄园', description='种出 10 个苹果',
            icon='🍏', color='#a5d6a7',
            requirement='种出 10 个苹果', requirement_type='apple_count',
            requirement_value=10, reward_points=50,
        ),
        Badge(
            name='阳光新芽', description='累计获得 100 阳光值',
            icon='✨', color='#fff59d',
            requirement='累计获得 100 阳光值', requirement_type='sunlight_earned_total',
            requirement_value=100, reward_points=20,
        ),
        Badge(
            name='阳光之星', description='当前拥有 300 阳光值',
            icon='🌤️', color='#ffcc80',
            requirement='当前拥有 300 阳光值', requirement_type='total_sunlight',
            requirement_value=300, reward_points=40,
        ),
    ]
    new_badges = [b for b in badges if b.name not in existing_names]
    if not new_badges:
        return 0
    db.add_all(new_badges)
    db.commit()
    return len(new_badges)


def seed_articles(db) -> int:
    """插入循证文章（若 t_articles 为空）。"""
    if db.query(Article).count() > 0:
        return 0

    articles = [
        Article(
            title='粗心不是态度问题，而是执行功能在发育', summary='从专注、组织、计划等执行功能维度理解孩子的粗心，给家长具体的观察指标。',
            content_url='https://example.com/articles/executive-function', category='executive',
            type='article', reading_time_minutes=6, image_url='', author='小树成长岛',
            published_at=datetime(2026, 1, 10),
        ),
        Article(
            title='如何用「家庭契约」替代说教与惩罚', summary='介绍共同制定规则、明确奖励边界的方法，避免过度物质化奖励。',
            content_url='https://example.com/articles/family-rules', category='parenting',
            type='article', reading_time_minutes=5, image_url='', author='小树成长岛',
            published_at=datetime(2026, 2, 3),
        ),
        Article(
            title='舒尔特方格训练法：每天 5 分钟提升专注', summary='带孩子玩 3×3 到 5×5 舒尔特方格，记录用时变化，提升视觉搜索与专注。',
            content_url='https://example.com/articles/schulte-grid', category='training',
            type='cbt', reading_time_minutes=4, image_url='', author='小树成长岛',
            published_at=datetime(2026, 3, 15),
        ),
        Article(
            title='物品收纳的「固定位置原则」', summary='给每样东西一个固定的家，用颜色贴纸做视觉提示，减少每天找东西的时间损耗。',
            content_url='https://example.com/articles/storage-principle', category='life_skill',
            type='article', reading_time_minutes=3, image_url='', author='小树成长岛',
            published_at=datetime(2026, 4, 22),
        ),
        Article(
            title='错题本的正确打开方式：3 天 7 天 14 天复习法', summary='基于记忆曲线的错题复习节奏，避免错题本变成抄写本。',
            content_url='https://example.com/articles/mistake-notebook', category='study',
            type='video', reading_time_minutes=7, image_url='', author='小树成长岛',
            published_at=datetime(2026, 5, 8),
        ),
    ]
    db.add_all(articles)
    db.commit()
    return len(articles)


def seed_initial_data(db) -> tuple[int, int]:
    return seed_badges(db), seed_articles(db)
