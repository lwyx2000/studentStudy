"""安全与数据一致性修复的回归测试。

覆盖本轮审计发现的问题：
- JWT 密钥不再退化成公开默认值
- 无密码的 child-login 端点已删除
- 密码强度校验
- 任务/习惯写接口仅家长可用
- 删除孩子 / 删除带子任务的任务不再 500
- 打卡积分由服务端按数据库分值重算（防改包刷分）
- 阳光扣减不透支
- 徽章「零丢失天数」不再算出负数
- 上传非图片被拒绝
- LLM endpoint 禁止指向内网（SSRF）
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SASession

from app.auth import create_access_token, hash_password
from app.config import Settings
from app.database import Base, engine
from app.main import app
from app.models import CheckIn, ItemLossRecord, Task, User
from app.routers.badges import _compute_requirement_progress
from app.services.llm import validate_endpoint

PASSWORD = 'pw123456'


@pytest.fixture(scope='module')
def ctx():
    Base.metadata.create_all(bind=engine)
    with SASession(engine) as s:
        parent = s.query(User).filter(User.login_name == 'sec_parent').first()
        if not parent:
            parent = User(
                name='安全测试家长', login_name='sec_parent', role='parent',
                password_hash=hash_password(PASSWORD), grade=0, is_onboarded=True,
            )
            s.add(parent)
            s.commit()
            s.refresh(parent)
        child = s.query(User).filter(User.login_name == 'sec_child').first()
        if not child:
            child = User(
                name='安全测试孩子', login_name='sec_child', role='child',
                password_hash=hash_password(PASSWORD), grade=3,
                fk_users_parent=parent.pk_users, is_onboarded=True,
            )
            s.add(child)
            s.commit()
            s.refresh(child)
        ids = {'parent': parent.pk_users, 'child': child.pk_users}

    c = TestClient(app)
    c.parent_headers = {'Authorization': f'Bearer {create_access_token(ids["parent"], "parent")}'}
    c.child_headers = {'Authorization': f'Bearer {create_access_token(ids["child"], "child")}'}
    c.parent_id = ids['parent']
    c.child_id = ids['child']
    yield c


def test_jwt_secret_not_default():
    s = Settings()
    assert s.jwt_secret not in {
        '', 'dev-secret-change-in-production', 'please-change-me-to-a-long-random-secret',
    }
    assert len(s.jwt_secret) >= 32


def test_child_login_removed(ctx):
    res = ctx.post(f'/api/v1/auth/child-login?child_id={ctx.child_id}&parent_id={ctx.parent_id}')
    assert res.status_code in (404, 405)


def test_register_requires_strong_password(ctx):
    # 密码太短 → 400（在邀请码校验之前就被拦截）
    res = ctx.post('/api/v1/auth/register?name=sec_new_parent&password=123')
    assert res.status_code == 400


def test_register_requires_invite_when_parent_exists(ctx):
    res = ctx.post('/api/v1/auth/register?name=sec_new_parent&password=abc12345')
    assert res.status_code == 403


def test_child_cannot_write_tasks(ctx):
    res = ctx.post('/api/v1/tasks/?title=伪造任务&type=study', headers=ctx.child_headers)
    assert res.status_code == 403


def test_child_cannot_write_habits(ctx):
    res = ctx.post(
        '/api/v1/habits/',
        json={'title': '伪造习惯', 'rewardPoints': 999},
        headers=ctx.child_headers,
    )
    assert res.status_code == 403


def test_delete_task_with_subtasks(ctx):
    res = ctx.post(
        f'/api/v1/tasks/?title=待删任务&type=study&child_id={ctx.child_id}',
        headers=ctx.parent_headers,
    )
    assert res.status_code == 201, res.text
    task_id = res.json()['task']['pk_tasks']
    res = ctx.post(
        f'/api/v1/tasks/{task_id}/subtasks?title=子项A',
        headers=ctx.parent_headers,
    )
    assert res.status_code == 201, res.text
    res = ctx.delete(f'/api/v1/tasks/{task_id}/permanent', headers=ctx.parent_headers)
    assert res.status_code == 200, res.text


def test_delete_child_cascades(ctx):
    with SASession(engine) as s:
        tmp = User(
            name='临时孩子', login_name='sec_tmp_child', role='child',
            password_hash=hash_password(PASSWORD), grade=3,
            fk_users_parent=ctx.parent_id,
        )
        s.add(tmp)
        s.commit()
        s.refresh(tmp)
        tmp_id = tmp.pk_users
        s.add(Task(
            fk_users=tmp_id, title='临时任务', type='study',
            assigned_date=date.today(), reward_points=5,
        ))
        s.commit()

    res = ctx.delete(f'/api/v1/children/{tmp_id}', headers=ctx.parent_headers)
    assert res.status_code == 200, res.text
    with SASession(engine) as s:
        assert s.query(User).filter(User.pk_users == tmp_id).first() is None
        assert s.query(Task).filter(Task.fk_users == tmp_id).count() == 0


def test_checkin_points_recomputed_from_db(ctx):
    """伪造 total_points 与单项分值都应被数据库真实分值覆盖。"""
    res = ctx.post(
        f'/api/v1/tasks/?title=重算任务&type=study&reward_points=10&child_id={ctx.child_id}',
        headers=ctx.parent_headers,
    )
    assert res.status_code == 201, res.text
    task_id = res.json()['task']['pk_tasks']
    # A：自定义 7 分；B：继承主任务 10 分（不勾选，用于避免触发「全部完成」）
    assert ctx.post(
        f'/api/v1/tasks/{task_id}/subtasks?title=重算子项A&reward_points=7',
        headers=ctx.parent_headers,
    ).status_code == 201
    assert ctx.post(
        f'/api/v1/tasks/{task_id}/subtasks?title=重算子项B',
        headers=ctx.parent_headers,
    ).status_code == 201

    payload = {
        'check_date': date.today().isoformat(),
        'total_points': 9999,
        'required_points': 9999,
        'optional_bonus': 0,
        'all_done_bonus': 10,
        'habit_points': 0,
        'task_count': 1,
        'completed_tasks': '[{"title":"重算子项A","points":9999,"icon":"📘"}]',
    }
    res = ctx.post('/api/v1/checkins/', params=payload, headers=ctx.child_headers)
    assert res.status_code == 200, res.text
    checkin = res.json()['checkin']
    assert checkin['total_points'] == 7
    assert checkin['required_points'] == 7
    assert checkin['all_done_bonus'] == 0

    # 清理，避免影响其他用例
    with SASession(engine) as s:
        s.query(CheckIn).filter(
            CheckIn.fk_users == ctx.child_id,
            CheckIn.check_date == date.today().isoformat(),
        ).delete()
        s.commit()
    ctx.delete(f'/api/v1/tasks/{task_id}/permanent', headers=ctx.parent_headers)


def test_sunlight_deduction_cannot_overdraw(ctx):
    with SASession(engine) as s:
        child = s.query(User).filter(User.pk_users == ctx.child_id).first()
        child.sunlight_points = 5
        s.commit()

    res = ctx.post(
        '/api/v1/points/award?amount=-50',
        headers=ctx.parent_headers,
    )
    assert res.status_code == 400
    with SASession(engine) as s:
        child = s.query(User).filter(User.pk_users == ctx.child_id).first()
        assert child.sunlight_points == 5


def test_zero_loss_days_not_negative(ctx):
    with SASession(engine) as s:
        child = s.query(User).filter(User.pk_users == ctx.child_id).first()
        s.query(CheckIn).filter(CheckIn.fk_users == child.pk_users).delete()
        s.query(ItemLossRecord).filter(ItemLossRecord.fk_users == child.pk_users).delete()
        s.add(CheckIn(
            fk_users=child.pk_users,
            check_date=date.today().isoformat(),
            total_points=10, status='approved', approved_at=datetime.now(),
        ))
        for i in range(3):
            s.add(ItemLossRecord(
                fk_users=child.pk_users, item_name=f'橡皮{i}',
                lost_location='学校', lost_date=date.today(),
            ))
        s.commit()
        s.refresh(child)
        progress = _compute_requirement_progress('zero_loss_days', 5, child, s)
        assert progress == 0  # 旧算法会算出 1 - 3 = -2


def test_upload_rejects_non_image(ctx):
    res = ctx.post(
        '/api/v1/mistakes/upload',
        files={'image': ('note.txt', b'hello world', 'text/plain')},
        headers=ctx.child_headers,
    )
    assert res.status_code == 400


def test_upload_accepts_png(ctx):
    png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
    res = ctx.post(
        '/api/v1/mistakes/upload',
        files={'image': ('shot.png', png, 'image/png')},
        headers=ctx.child_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()['imageUrl'].startswith('/uploads/mistake_')
    assert '.png' in res.json()['imageUrl']


@pytest.mark.parametrize('endpoint', ['http://127.0.0.1:8000/v1', 'http://192.168.3.53/v1', 'http://169.254.169.254/latest'])
def test_llm_endpoint_rejects_private(endpoint):
    with pytest.raises(ValueError):
        validate_endpoint(endpoint, allow_private=False)


def test_llm_endpoint_allows_public():
    assert validate_endpoint('https://api.openai.com/v1') == 'https://api.openai.com/v1'
