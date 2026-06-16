from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import HabitSOP, SOPStep, User

router = APIRouter()


@router.get('/current')
def get_current_habit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = db.query(HabitSOP).order_by(HabitSOP.created_at.desc()).first()
    if not habit:
        raise HTTPException(status_code=404, detail='暂无当前习惯')
    steps = db.query(SOPStep).filter(SOPStep.fk_habit_sops == habit.pk_habit_sops).order_by(SOPStep.order).all()
    return {
        'habit': {
            'pk_habit_sops': habit.pk_habit_sops,
            'title': habit.title,
            'week_number': habit.week_number,
            'grade_range': habit.grade_range,
            'difficulty_level': habit.difficulty_level,
            'created_at': habit.created_at,
            'steps': [
                {'order': s.order, 'instruction': s.instruction, 'imageUrl': s.image_url, 'gifUrl': s.gif_url}
                for s in steps
            ],
        }
    }


@router.put('/current')
def update_current_habit(
    title: str | None = None,
    week_number: int | None = None,
    grade_range: str | None = None,
    difficulty_level: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(HabitSOP).order_by(HabitSOP.created_at.desc()).first()
    if not habit:
        raise HTTPException(status_code=404, detail='暂无当前习惯')
    if title is not None:
        habit.title = title
    if week_number is not None:
        habit.week_number = week_number
    if grade_range is not None:
        habit.grade_range = grade_range
    if difficulty_level is not None:
        habit.difficulty_level = difficulty_level
    db.commit()
    db.refresh(habit)
    return {'habit': habit}


@router.post('/', status_code=201)
def create_habit(
    title: str,
    week_number: int = 1,
    grade_range: str = '1-3',
    difficulty_level: int = 2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = HabitSOP(title=title, week_number=week_number, grade_range=grade_range, difficulty_level=difficulty_level)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return {'habit': habit}


@router.get('/history')
def get_habit_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habits = db.query(HabitSOP).order_by(HabitSOP.created_at.desc()).all()
    return {'history': habits}
