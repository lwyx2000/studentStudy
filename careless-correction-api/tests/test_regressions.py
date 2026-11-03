"""第二轮审计修复的回归测试。

覆盖：
- 打卡快照里同一条小任务重复提交会被重复计分（可把阳光值刷成 N 倍）
- 不同主任务下同名小任务分值不同时，按标题匹配会算错（应按子任务 id 计分）
- 周六被当成工作日，与前端口径不一致
- 保存 LLM 配置时把占位符 `***` 当成真实 Key 写库，覆盖掉真实 Key
- 永久删除被任务引用的习惯触发外键错误（500）
- 艾宾浩斯复习间隔少算一档
- 负数的物品兑换价 / 小任务分值
"""
import json
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SASession

from app.auth import create_access_token, hash_password
from app.database import Base, engine
from app.main import app
from app.models import HabitSOP, LlmConfig, MistakeRecord, SOPStep, SubTask, Task, User
from app.routers.mistakes import _get_next_review_interval
from app.routers.tasks import _matches_week_day

PASSWORD = 'pw123456'


@pytest.fixture(scope='module')
def ctx():
    Base.metadata.create_all(bind=engine)
    with SASession(engine) as s:
        parent = s.query(User).filter(User.login_name == 'rg_parent').first()
        if not parent:
            parent = User(
                name='回归家长', login_name='rg_parent', role='parent',
                password_hash=hash_password(PASSWORD), grade=0, is_onboarded=True,
            )
            s.add(parent)
            s.commit()
            s.refresh(parent)
        child = s.query(User).filter(User.login_name == 'rg_child').first()
        if not child:
            child = User(
                name='回归孩子', login_name='rg_child', role='child',
                password_hash=hash_password(PASSWORD), grade=3,
                fk_users_parent=parent.pk_users, is_onboarded=True,
            )
            s.add(child)
            s.commit()
            s.refresh(child)
        ids = {'parent': parent.pk_users, 'child': child.pk_users}

    c = TestClient(app)
    c.child_headers = {'Authorization': f'Bearer {create_access_token(ids["child"], "child")}'}
    c.parent_headers = {'Authorization': f'Bearer {create_access_token(ids["parent"], "parent")}'}
    c.headers.update(c.child_headers)
    c.child_id = ids['child']
    c.parent_id = ids['parent']
    yield c

    with SASession(engine) as s:
        s.query(SubTask).filter(
            SubTask.fk_tasks.in_(s.query(Task.pk_tasks).filter(Task.fk_users == ids['child']))
        ).delete(synchronize_session=False)
        s.query(Task).filter(Task.fk_users == ids['child']).delete(synchronize_session=False)
        s.query(SOPStep).filter(
            SOPStep.fk_habit_sops.in_(
                s.query(HabitSOP.pk_habit_sops).filter(HabitSOP.fk_users == ids['child'])
            )
        ).delete(synchronize_session=False)
        s.query(HabitSOP).filter(HabitSOP.fk_users == ids['child']).delete(synchronize_session=False)
        # 复习记录引用错题（无级联），必须先删复习记录再删错题
        from app.models import MistakeReview
        s.query(MistakeReview).filter(
            MistakeReview.fk_mistake_records.in_(
                s.query(MistakeRecord.pk_mistake_records).filter(MistakeRecord.fk_users == ids['child'])
            )
        ).delete(synchronize_session=False)
        s.query(MistakeRecord).filter(MistakeRecord.fk_users == ids['child']).delete(synchronize_session=False)
        s.query(LlmConfig).filter(LlmConfig.fk_users == ids['parent']).delete(synchronize_session=False)
        s.commit()


def _seed_task(db, child_id, title, points, sub_titles):
    """建一个主任务 + 若干必做小任务，返回 (task_id, [subtask_id...])"""
    task = Task(fk_users=child_id, title=title, type='study', reward_points=points, assigned_date=date.today())
    db.add(task)
    db.commit()
    db.refresh(task)
    ids = []
    for st in sub_titles:
        sub = SubTask(fk_tasks=task.pk_tasks, title=st, type='study')
        db.add(sub)
        db.commit()
        db.refresh(sub)
        ids.append(sub.pk_task_ids if False else sub.pk_sub_tasks)
    return task.pk_tasks, ids


def test_duplicate_snapshot_items_are_counted_once(ctx):
    """同一条小任务在快照里重复 N 次，只能计一次分。"""
    with SASession(engine) as s:
        _task_id, (sub_id,) = _seed_task(s, ctx.child_id, '重复计分任务', 10, ['重复-口算一页'])

    item = {'title': '重复-口算一页', 'icon': '📋', 'points': 10, 'subTaskId': str(sub_id)}
    resp = ctx.post('/api/v1/checkins/submit', json={
        'check_date': date.today().isoformat(),
        'total_points': 50,
        'completed_tasks': [item] * 5,
    })
    assert resp.status_code == 200
    body = resp.json()['checkin']
    # 必做小任务只应计一次 10 分；旧实现会把重复项各算一遍（5×10=50）
    assert body['requiredPoints'] == 10
    assert body['totalPoints'] <= 20
    assert len(body['completedTasksSnapshot']) == 1  # 重复项在清洗阶段就被丢掉


def test_same_title_different_subtask_id_scores_separately(ctx):
    """两个主任务下有同名小任务、分值不同时，按 id 分别计分。"""
    with SASession(engine) as s:
        _t1, (a,) = _seed_task(s, ctx.child_id, '语文任务', 3, ['同名小任务'])
        _t2, (b,) = _seed_task(s, ctx.child_id, '数学任务', 10, ['同名小任务'])

    resp = ctx.post('/api/v1/checkins/submit', json={
        'check_date': date.today().isoformat(),
        'total_points': 999,
        'completed_tasks': [
            {'title': '同名小任务', 'subTaskId': str(a)},
            {'title': '同名小任务', 'subTaskId': str(b)},
        ],
    })
    assert resp.status_code == 200
    body = resp.json()['checkin']
    # 按 id 匹配才能拿到 3 + 10；旧实现按标题匹配会把两条都算成第一条的分值（3+3 或 10+10）
    assert body['requiredPoints'] == 13
    assert body['totalPoints'] >= 13


def test_query_style_submit_still_works(ctx):
    """旧客户端用 query 参数提交，仍需保留兼容。"""
    resp = ctx.post('/api/v1/checkins/', params={
        'check_date': date.today().isoformat(),
        'completed_tasks': json.dumps([{'title': '不存在的任务'}]),
    })
    assert resp.status_code == 200
    assert resp.json()['checkin']['totalPoints'] == 0


def test_saturday_is_not_weekday():
    # 2026-11-07 是周六、2026-11-08 是周日
    assert _matches_week_day('weekday', date(2026, 11, 7)) is False
    assert _matches_week_day('weekend', date(2026, 11, 7)) is True
    assert _matches_week_day('weekday', date(2026, 11, 6)) is True
    assert _matches_week_day('weekend', date(2026, 11, 8)) is True


def test_llm_placeholder_key_does_not_overwrite_real_key(ctx):
    """前端把 `***` 原样回传时，真实 Key 必须保持不变。"""
    r1 = ctx.put('/api/v1/llm/config', params={
        'endpoint': 'https://api.example.com/v1',
        'api_key': 'sk-real-key',
        'model': 'gpt-4o-mini',
        'enabled': 'true',
    }, headers=ctx.parent_headers)
    assert r1.status_code == 200

    got = ctx.get('/api/v1/llm/config', headers=ctx.parent_headers).json()['config']
    assert got['apiKey'] == '***'

    # 前端保存时把占位符一起传回来（此前会把真实 Key 覆盖成 ***）
    r2 = ctx.put('/api/v1/llm/config', params={'api_key': '***', 'enabled': 'true'},
                 headers=ctx.parent_headers)
    assert r2.status_code == 200

    with SASession(engine) as s:
        cfg = s.query(LlmConfig).filter(LlmConfig.fk_users == ctx.parent_id).first()
        assert cfg.api_key == 'sk-real-key'


def test_delete_habit_referenced_by_task(ctx):
    """任务引用习惯时永久删除习惯不能 500（开启 foreign_keys=ON 后曾必现）。"""
    with SASession(engine) as s:
        habit = HabitSOP(fk_users=ctx.child_id, title='被引用的习惯', grade_range='1-3',
                         difficulty_level=2, reward_points=5)
        s.add(habit)
        s.commit()
        s.refresh(habit)
        s.add(SOPStep(fk_habit_sops=habit.pk_habit_sops, order=1, instruction='第一步'))
        task = Task(fk_users=ctx.child_id, title='引用习惯的任务', type='study',
                    reward_points=5, assigned_date=date.today(), fk_habit_sops=habit.pk_habit_sops)
        s.add(task)
        s.commit()
        habit_id = habit.pk_habit_sops

    resp = ctx.delete(f'/api/v1/habits/{habit_id}/permanent', headers=ctx.parent_headers)
    assert resp.status_code == 200
    with SASession(engine) as s:
        assert s.query(HabitSOP).filter(HabitSOP.pk_habit_sops == habit_id).first() is None
        t = s.query(Task).filter(Task.title == '引用习惯的任务').first()
        assert t is not None and t.fk_habit_sops is None


def test_review_interval_first_review_is_three_days():
    assert _get_next_review_interval(1) == 3
    assert _get_next_review_interval(2) == 7
    assert _get_next_review_interval(3) == 14
    assert _get_next_review_interval(4) == 30
    assert _get_next_review_interval(9) == 30


def test_negative_reward_cost_rejected(ctx):
    resp = ctx.post('/api/v1/points/rewards', params={'name': '倒贴', 'cost': -100})
    assert resp.status_code == 400


def test_subtask_negative_points_rejected(ctx):
    with SASession(engine) as s:
        task = Task(fk_users=ctx.child_id, title='分值校验任务', type='study',
                    reward_points=5, assigned_date=date.today())
        s.add(task)
        s.commit()
        task_id = task.pk_tasks

    resp = ctx.post(f'/api/v1/tasks/{task_id}/subtasks',
                    params={'title': '异常分值', 'reward_points': -5},
                    headers=ctx.parent_headers)
    assert resp.status_code == 400


# ── 第三轮补充：输入校验加固 ────────────────────────────────────────────

def test_mistake_invalid_image_url_rejected(ctx):
    """image_url 只接受本服务上传路径或 http(s) 地址，不能塞任意字符串"""
    resp = ctx.post('/api/v1/mistakes/', params={'subject': '数学', 'image_url': 'javascript:alert(1)'})
    assert resp.status_code == 400
    resp = ctx.post('/api/v1/mistakes/', params={'subject': '数学', 'image_url': 'x' * 300})
    assert resp.status_code == 400
    resp = ctx.post('/api/v1/mistakes/', params={'subject': '数学', 'image_url': '/uploads/mistake_abc.png'})
    assert resp.status_code == 201
    # 超长科目被截断而不是报错
    resp = ctx.post('/api/v1/mistakes/', params={'subject': '长' * 60, 'image_url': '/uploads/mistake_abc.png'})
    assert resp.status_code == 201


def test_mistake_review_confidence_clamped(ctx):
    """信心等级越界（如 99）应收敛到 1-5 而不是 500 或原样入库"""
    with SASession(engine) as s:
        rec = MistakeRecord(fk_users=ctx.child_id, subject='语文', image_url='/uploads/x.png')
        s.add(rec)
        s.commit()
        rec_id = rec.pk_mistake_records
    resp = ctx.post(f'/api/v1/mistakes/{rec_id}/review',
                    params={'can_resolve': 'false', 'confidence_level': 99})
    assert resp.status_code == 200
    body = resp.json()
    assert body['review']['confidence_level'] == 5


def test_reward_name_validated(ctx):
    """空名称拒绝，超长名称截断到 100"""
    resp = ctx.post('/api/v1/points/rewards', params={'name': '   ', 'cost': 10})
    assert resp.status_code == 400
    resp = ctx.post('/api/v1/points/rewards', params={'name': '名' * 300, 'cost': 10})
    assert resp.status_code == 201
    assert len(resp.json()['reward']['name']) <= 100


def test_add_child_duplicate_after_strip(ctx):
    """带空格的同名孩子也应命中去重校验"""
    resp = ctx.post('/api/v1/children/', params={'name': '去重孩子'},
                    headers=ctx.parent_headers)
    assert resp.status_code == 201
    resp = ctx.post('/api/v1/children/', params={'name': ' 去重孩子 '},
                    headers=ctx.parent_headers)
    assert resp.status_code == 409
