from datetime import date, datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    pk_users: int
    name: str
    login_name: str | None = None
    role: str
    grade: int | None = None
    avatar_url: str | None = None
    sunlight_points: int = 0
    apples: int = 0
    streak_days: int = 0
    is_onboarded: bool = False
    fk_users_parent: int | None = None

    model_config = {'from_attributes': True}


class ChildOut(BaseModel):
    pk_users: int
    name: str
    login_name: str | None = None
    grade: int | None = None
    avatar_url: str | None = None
    sunlight_points: int = 0
    apples: int = 0
    streak_days: int = 0
    is_onboarded: bool = False

    model_config = {'from_attributes': True}


class TokenOut(BaseModel):
    token: str
    user: UserOut


class SubTaskOut(BaseModel):
    pk_sub_tasks: int
    title: str
    type: str
    week_day: str | None = None
    sort_order: int = 0

    model_config = {'from_attributes': True}


class TaskOut(BaseModel):
    pk_tasks: int
    title: str
    description: str | None = None
    type: str
    status: str = 'pending'
    reward_points: int = 10
    icon: str | None = None
    week_day: str | None = None
    assigned_date: date
    completed_at: datetime | None = None
    completion_photo_url: str | None = None
    active: bool = True
    created_at: datetime | None = None
    sub_tasks: list[SubTaskOut] = []

    model_config = {'from_attributes': True}


class HabitOut(BaseModel):
    pk_habit_sops: int
    title: str
    grade_range: str
    difficulty_level: int
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class StepOut(BaseModel):
    pk_sop_steps: int
    order: int
    instruction: str
    image_url: str | None = None
    gif_url: str | None = None

    model_config = {'from_attributes': True}


class HabitDetailOut(HabitOut):
    steps: list[StepOut] = []


class MistakeOut(BaseModel):
    pk_mistake_records: int
    subject: str
    image_url: str
    is_carelessness: bool = True
    category: str | None = None
    knowledge_point: str | None = None
    grade: int | None = None
    review_strategy: str = '3day-repeat'
    next_review_at: datetime | None = None
    review_count: int = 0
    resolved: bool = False
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class ItemLossOut(BaseModel):
    pk_item_loss_records: int
    item_name: str
    lost_location: str
    estimated_cost: float = 0
    lost_date: date
    frequency_30d: int = 1
    is_high_frequency: bool = False

    model_config = {'from_attributes': True}


class ItemStorageOut(BaseModel):
    pk_item_storage_records: int
    item_name: str
    storage_location: str
    notes: str | None = None
    storage_date: date
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class SunlightHistoryOut(BaseModel):
    pk_sunlight_history: int
    amount: int
    reason: str
    type: str
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class AppleHistoryOut(BaseModel):
    pk_apple_history: int
    amount: int
    reason: str
    type: str
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class RewardItemOut(BaseModel):
    pk_reward_items: int
    name: str
    description: str | None = None
    cost: int
    icon: str | None = None
    active: bool = True

    model_config = {'from_attributes': True}


class BadgeOut(BaseModel):
    pk_badges: int
    name: str
    description: str
    icon: str
    color: str
    requirement: str
    unlocked: bool = False
    unlocked_at: datetime | None = None
    reward_points: int = 50

    model_config = {'from_attributes': True}


class GrowthSnapshotOut(BaseModel):
    pk_growth_snapshots: int
    snapshot_date: date
    mistake_rate: float | None = None
    item_loss_rate: int | None = None
    task_completion_rate: float | None = None

    model_config = {'from_attributes': True}


class DiagnosticAlertOut(BaseModel):
    pk_diagnostic_alerts: int
    title: str
    description: str
    suggestion: str
    severity: str
    is_read: bool = False
    created_at: datetime | None = None

    model_config = {'from_attributes': True}


class LlmConfigOut(BaseModel):
    pk_llm_config: int | None = None
    endpoint: str
    model: str
    mistake_prompt: str
    assessment_prompt: str
    assessment_cron: str = 'weekly'
    enabled: bool = False
    apiKey: str = ''

    model_config = {'from_attributes': True}


class ParentSettingsOut(BaseModel):
    pk_parent_settings: int | None = None
    daily_reminder: bool = True
    achievement_notification: bool = True
    weekly_report: bool = True
    school_sync: bool = False
    school_sync_code: str | None = None

    model_config = {'from_attributes': True}


class ArticleOut(BaseModel):
    pk_articles: int
    title: str
    summary: str | None = None
    content_url: str
    category: str
    type: str
    reading_time_minutes: int | None = None
    image_url: str | None = None
    author: str | None = None

    model_config = {'from_attributes': True}
