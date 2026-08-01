from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import HabitSOP, SOPStep, User

router = APIRouter()


def resolve_target(current_user: User, child_id: int | None, db: Session) -> User:
    if child_id is None:
        return current_user
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail='无权访问')
    child = db.query(User).filter(
        User.pk_users == child_id,
        User.fk_users_parent == current_user.pk_users,
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail='孩子账号不存在')
    return child


class StepInput(BaseModel):
    instruction: str
    order: int
    image_url: str | None = Field(default=None, alias='imageUrl')
    gif_url: str | None = Field(default=None, alias='gifUrl')

    model_config = {'populate_by_name': True}


class HabitCreateInput(BaseModel):
    title: str
    grade_range: str = Field(default='1-3', alias='gradeRange')
    difficulty_level: int = Field(default=2, alias='difficultyLevel')
    reward_points: int = Field(default=5, alias='rewardPoints')
    steps: list[StepInput] = []

    model_config = {'populate_by_name': True}


class HabitUpdateInput(BaseModel):
    title: str | None = None
    grade_range: str | None = Field(default=None, alias='gradeRange')
    difficulty_level: int | None = Field(default=None, alias='difficultyLevel')
    reward_points: int | None = Field(default=None, alias='rewardPoints')
    active: bool | None = None
    steps: list[StepInput] | None = None

    model_config = {'populate_by_name': True}


def _habit_to_dict(habit: HabitSOP, steps: list[SOPStep]) -> dict:
    return {
        'pk_habit_sops': habit.pk_habit_sops,
        'title': habit.title,
        'grade_range': habit.grade_range,
        'difficulty_level': habit.difficulty_level,
        'reward_points': habit.reward_points,
        'created_at': habit.created_at,
        'steps': [
            {
                'order': s.order,
                'instruction': s.instruction,
                'image_url': s.image_url,
                'gif_url': s.gif_url,
            }
            for s in steps
        ],
    }


@router.get('/')
def list_habits(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    habits = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.fk_users == target.pk_users, HabitSOP.active == True)
        .order_by(HabitSOP.created_at.desc())
        .all()
    )
    return {'habits': [_habit_to_dict(h, h.steps) for h in habits]}


@router.get('/inventory')
def list_habits_inventory(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有习惯（包括 inactive 的），用于习惯清单页面"""
    target = resolve_target(current_user, child_id, db)
    habits = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.fk_users == target.pk_users)
        .order_by(HabitSOP.active.desc(), HabitSOP.created_at.desc())
        .all()
    )
    return {'habits': [_habit_to_dict(h, h.steps) for h in habits]}


@router.put('/{habit_id}')
def update_habit(
    habit_id: int,
    data: HabitUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.pk_habit_sops == habit_id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='习惯不存在')
    if data.title is not None:
        habit.title = data.title
    if data.grade_range is not None:
        habit.grade_range = data.grade_range
    if data.difficulty_level is not None:
        habit.difficulty_level = data.difficulty_level
    if data.reward_points is not None:
        habit.reward_points = data.reward_points
    if data.active is not None:
        habit.active = data.active

    if data.steps is not None:
        db.query(SOPStep).filter(SOPStep.fk_habit_sops == habit.pk_habit_sops).delete()
        for s in data.steps:
            db.add(SOPStep(
                fk_habit_sops=habit.pk_habit_sops,
                order=s.order,
                instruction=s.instruction,
                image_url=s.image_url,
                gif_url=s.gif_url,
            ))

    db.commit()
    db.refresh(habit)
    steps = (
        db.query(SOPStep)
        .filter(SOPStep.fk_habit_sops == habit.pk_habit_sops)
        .order_by(SOPStep.order)
        .all()
    )
    return {'habit': _habit_to_dict(habit, steps)}


@router.post('/', status_code=201)
def create_habit(
    data: HabitCreateInput,
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = resolve_target(current_user, child_id, db)
    habit = HabitSOP(
        fk_users=target.pk_users,
        title=data.title,
        grade_range=data.grade_range,
        difficulty_level=data.difficulty_level,
        reward_points=data.reward_points,
    )
    db.add(habit)
    db.flush()

    for s in data.steps:
        db.add(SOPStep(
            fk_habit_sops=habit.pk_habit_sops,
            order=s.order,
            instruction=s.instruction,
            image_url=s.image_url,
            gif_url=s.gif_url,
        ))

    db.commit()
    db.refresh(habit)
    steps = (
        db.query(SOPStep)
        .filter(SOPStep.fk_habit_sops == habit.pk_habit_sops)
        .order_by(SOPStep.order)
        .all()
    )
    return {'habit': _habit_to_dict(habit, steps)}


@router.delete('/{habit_id}')
def delete_habit(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """软删除：将习惯标记为 inactive"""
    habit = (
        db.query(HabitSOP)
        .filter(HabitSOP.pk_habit_sops == habit_id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='习惯不存在')
    habit.active = False
    db.commit()
    return {'ok': True, 'softDelete': True}


@router.delete('/{habit_id}/permanent')
def delete_habit_permanent(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """永久删除习惯（仅从清单页面调用）"""
    habit = (
        db.query(HabitSOP)
        .filter(HabitSOP.pk_habit_sops == habit_id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='习惯不存在')
    db.query(SOPStep).filter(SOPStep.fk_habit_sops == habit_id).delete()
    db.delete(habit)
    db.commit()
    return {'ok': True}


@router.get('/steps/library')
def get_step_library(
    child_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有习惯步骤库（用于复用）"""
    target = resolve_target(current_user, child_id, db)
    steps = (
        db.query(SOPStep)
        .join(HabitSOP, SOPStep.fk_habit_sops == HabitSOP.pk_habit_sops)
        .filter(HabitSOP.fk_users == target.pk_users)
        .order_by(SOPStep.pk_sop_steps.desc())
        .all()
    )
    return {'steps': [
        {
            'pk_sop_steps': s.pk_sop_steps,
            'order': s.order,
            'instruction': s.instruction,
            'image_url': s.image_url,
            'gif_url': s.gif_url,
            'habit_title': db.query(HabitSOP.title).filter(HabitSOP.pk_habit_sops == s.fk_habit_sops).scalar(),
        }
        for s in steps
    ]}


@router.get('/{habit_id}')
def get_habit_detail(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .filter(HabitSOP.pk_habit_sops == habit_id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='习惯不存在')
    return {'habit': _habit_to_dict(habit, habit.steps)}
