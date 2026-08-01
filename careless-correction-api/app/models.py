from datetime import date, datetime, timedelta

from sqlalchemy import (
    Boolean, Date, DateTime, DECIMAL, Float, ForeignKey, Integer, JSON,
    SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = 't_users'

    pk_users: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    login_name: Mapped[str | None] = mapped_column(String(50), unique=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    fk_users_parent: Mapped[int | None] = mapped_column(Integer, ForeignKey('t_users.pk_users'))
    sunlight_points: Mapped[int] = mapped_column(Integer, default=0)
    apples: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent = relationship('User', remote_side='User.pk_users', backref='children')


class Assessment(Base):
    __tablename__ = 't_assessments'

    pk_assessments: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    focus_attention: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    organization: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    emotional_control: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    planning: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    impulse_control: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    recommended_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    task_density: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default='initial')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='assessments')


class HabitSOP(Base):
    __tablename__ = 't_habit_sops'

    pk_habit_sops: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_range: Mapped[str] = mapped_column(String(10), nullable=False)
    difficulty_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    reward_points: Mapped[int] = mapped_column(SmallInteger, default=5)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    fk_users: Mapped[int | None] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=True)

    steps = relationship('SOPStep', backref='habit', cascade='all, delete-orphan')
    tasks = relationship('Task', backref='habit_sop_rel')
    user = relationship('User', backref='habits')


class SOPStep(Base):
    __tablename__ = 't_sop_steps'

    pk_sop_steps: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_habit_sops: Mapped[int] = mapped_column(Integer, ForeignKey('t_habit_sops.pk_habit_sops'), nullable=False)
    order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255))
    gif_url: Mapped[str | None] = mapped_column(String(255))


class Task(Base):
    __tablename__ = 't_tasks'

    pk_tasks: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    reward_points: Mapped[int] = mapped_column(SmallInteger, default=10)
    icon: Mapped[str | None] = mapped_column(String(50))
    week_day: Mapped[str | None] = mapped_column(String(50))
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    completion_photo_url: Mapped[str | None] = mapped_column(String(255))
    fk_habit_sops: Mapped[int | None] = mapped_column(Integer, ForeignKey('t_habit_sops.pk_habit_sops'))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship('User', backref='tasks')


class SubTask(Base):
    __tablename__ = 't_sub_tasks'

    pk_sub_tasks: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_tasks: Mapped[int] = mapped_column(Integer, ForeignKey('t_tasks.pk_tasks'), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    week_day: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task = relationship('Task', backref='sub_tasks')


class MistakeRecord(Base):
    __tablename__ = 't_mistake_records'

    pk_mistake_records: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    subject: Mapped[str] = mapped_column(String(30), nullable=False)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    recognized_text: Mapped[str | None] = mapped_column(Text)
    is_carelessness: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[str | None] = mapped_column(String(30))
    knowledge_point: Mapped[str | None] = mapped_column(String(100))
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    curriculum_chapter: Mapped[str | None] = mapped_column(String(100))
    review_strategy: Mapped[str] = mapped_column(String(30), default='3day-repeat')
    next_review_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now() + timedelta(days=3))
    review_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='mistake_records')
    reviews = relationship('MistakeReview', backref='mistake', cascade='all, delete-orphan')


class MistakeReview(Base):
    __tablename__ = 't_mistake_reviews'

    pk_mistake_reviews: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_mistake_records: Mapped[int] = mapped_column(Integer, ForeignKey('t_mistake_records.pk_mistake_records'), nullable=False)
    can_resolve_now: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_level: Mapped[int | None] = mapped_column(SmallInteger)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime)


class ItemStorageRecord(Base):
    __tablename__ = 't_item_storage_records'

    pk_item_storage_records: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_location: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    storage_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='storage_records')


class ItemLossRecord(Base):
    __tablename__ = 't_item_loss_records'

    pk_item_loss_records: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    lost_location: Mapped[str] = mapped_column(String(30), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    lost_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    frequency_30d: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_high_frequency: Mapped[bool] = mapped_column(Boolean, default=False)
    suggestion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='loss_records')


class RewardItem(Base):
    __tablename__ = 't_reward_items'

    pk_reward_items: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship('User', backref='reward_items')


class SunlightHistory(Base):
    __tablename__ = 't_sunlight_history'

    pk_sunlight_history: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='sunlight_history')


class CheckIn(Base):
    __tablename__ = 't_check_ins'

    pk_check_ins: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    check_date: Mapped[str] = mapped_column(String(20), nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    habit_step_count: Mapped[int] = mapped_column(Integer, default=0)
    task_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship('User', backref='check_ins')


class LlmConfig(Base):
    __tablename__ = 't_llm_config'

    pk_llm_config: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), unique=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    mistake_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_cron: Mapped[str] = mapped_column(String(10), default='weekly')
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship('User', backref='llm_config')


class GrowthSnapshot(Base):
    __tablename__ = 't_growth_snapshots'

    pk_growth_snapshots: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    mistake_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 4))
    item_loss_rate: Mapped[int | None] = mapped_column(SmallInteger)
    task_completion_rate: Mapped[float | None] = mapped_column(DECIMAL(5, 4))
    focus_score: Mapped[int | None] = mapped_column(SmallInteger)
    neatness_score: Mapped[int | None] = mapped_column(SmallInteger)
    metacognition_score: Mapped[int | None] = mapped_column(SmallInteger)
    emotion_score: Mapped[int | None] = mapped_column(SmallInteger)
    source: Mapped[str] = mapped_column(String(20), default='daily')

    user = relationship('User', backref='growth_snapshots')

    __table_args__ = (
        UniqueConstraint('fk_users', 'snapshot_date', 'source', name='uq_growth_snapshot'),
    )


class DiagnosticAlert(Base):
    __tablename__ = 't_diagnostic_alerts'

    pk_diagnostic_alerts: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    related_metric: Mapped[str | None] = mapped_column(String(50))
    metric_change: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='alerts')


class Badge(Base):
    __tablename__ = 't_badges'

    pk_badges: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    requirement_value: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_points: Mapped[int] = mapped_column(SmallInteger, default=50)

    unlocks = relationship('BadgeUnlock', backref='badge', cascade='all, delete-orphan')


class BadgeUnlock(Base):
    __tablename__ = 't_badge_unlocks'

    pk_badge_unlocks: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    fk_badges: Mapped[int] = mapped_column(Integer, ForeignKey('t_badges.pk_badges'), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='badge_unlocks')

    __table_args__ = (
        UniqueConstraint('fk_users', 'fk_badges', name='uq_badge_unlocks'),
    )


class ParentSetting(Base):
    __tablename__ = 't_parent_settings'

    pk_parent_settings: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), unique=True, nullable=False)
    daily_reminder: Mapped[bool] = mapped_column(Boolean, default=True)
    achievement_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_report: Mapped[bool] = mapped_column(Boolean, default=True)
    school_sync: Mapped[bool] = mapped_column(Boolean, default=False)
    school_sync_code: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship('User', backref='parent_settings')


class Article(Base):
    __tablename__ = 't_articles'

    pk_articles: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content_url: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    reading_time_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    image_url: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(100))
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    bookmarks = relationship('ArticleBookmark', backref='article', cascade='all, delete-orphan')


class ArticleBookmark(Base):
    __tablename__ = 't_article_bookmarks'

    pk_article_bookmarks: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    fk_articles: Mapped[int] = mapped_column(Integer, ForeignKey('t_articles.pk_articles'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='bookmarks')

    __table_args__ = (
        UniqueConstraint('fk_users', 'fk_articles', name='uq_article_bookmarks'),
    )


class GrowthReport(Base):
    __tablename__ = 't_growth_reports'

    pk_growth_reports: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    pdf_url: Mapped[str] = mapped_column(String(255), nullable=False)
    include_peer_comparison: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='growth_reports')


class TaskWeeklyProgress(Base):
    __tablename__ = 't_task_weekly_progress'

    pk_task_weekly_progress: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    week_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    completed_days: Mapped[int] = mapped_column(SmallInteger, default=0)
    total_days: Mapped[int] = mapped_column(SmallInteger, default=7)
    progress_percent: Mapped[float] = mapped_column(DECIMAL(5, 2), default=0)
    fk_habit_sops: Mapped[int | None] = mapped_column(Integer, ForeignKey('t_habit_sops.pk_habit_sops'))

    user = relationship('User', backref='weekly_progress')
    habit = relationship('HabitSOP', backref='weekly_progress')

    __table_args__ = (
        UniqueConstraint('fk_users', 'year', 'week_number', name='uq_weekly_progress'),
    )


class AppleHistory(Base):
    __tablename__ = 't_apple_history'

    pk_apple_history: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fk_users: Mapped[int] = mapped_column(Integer, ForeignKey('t_users.pk_users'), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'grow' or 'redeem'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship('User', backref='apple_history')
