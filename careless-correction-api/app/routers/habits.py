from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import HabitSOP, SOPStep, User

router = APIRouter()


class StepInput(BaseModel):
    instruction: str
    order: int
    image_url: str | None = Field(default=None, alias='imageUrl')
    gif_url: str | None = Field(default=None, alias='gifUrl')

    model_config = {'populate_by_name': True}


class HabitCreateInput(BaseModel):
    title: str
    week_number: int = Field(default=1, alias='weekNumber')
    grade_range: str = Field(default='1-3', alias='gradeRange')
    difficulty_level: int = Field(default=2, alias='difficultyLevel')
    steps: list[StepInput] = []

    model_config = {'populate_by_name': True}


class HabitUpdateInput(BaseModel):
    title: str | None = None
    week_number: int | None = Field(default=None, alias='weekNumber')
    grade_range: str | None = Field(default=None, alias='gradeRange')
    difficulty_level: int | None = Field(default=None, alias='difficultyLevel')
    steps: list[StepInput] | None = None

    model_config = {'populate_by_name': True}


def _habit_to_dict(habit: HabitSOP, steps: list[SOPStep]) -> dict:
    return {
        'pk_habit_sops': habit.pk_habit_sops,
        'title': habit.title,
        'week_number': habit.week_number,
        'grade_range': habit.grade_range,
        'difficulty_level': habit.difficulty_level,
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


@router.get('/current')
def get_current_habit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .order_by(HabitSOP.created_at.desc())
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='暂无当前习惯')
    return {'habit': _habit_to_dict(habit, habit.steps)}


@router.put('/current')
def update_current_habit(
    data: HabitUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .order_by(HabitSOP.created_at.desc())
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail='暂无当前习惯')
    if data.title is not None:
        habit.title = data.title
    if data.week_number is not None:
        habit.week_number = data.week_number
    if data.grade_range is not None:
        habit.grade_range = data.grade_range
    if data.difficulty_level is not None:
        habit.difficulty_level = data.difficulty_level

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = HabitSOP(
        title=data.title,
        week_number=data.week_number,
        grade_range=data.grade_range,
        difficulty_level=data.difficulty_level,
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


@router.get('/history')
def get_habit_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habits = (
        db.query(HabitSOP)
        .options(selectinload(HabitSOP.steps))
        .order_by(HabitSOP.created_at.desc())
        .all()
    )
    return {'history': [_habit_to_dict(h, h.steps) for h in habits]}


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
