"""打卡审批 / 连续天数 / 阳光发放的回归测试。

覆盖几个曾经的坑：
- 补打卡历史日期会把已有连续天数覆盖成小数（streak 必须以今天为锚点重算）
- 未来日期可以打卡（提前刷阳光）
- 同一条打卡重复审批重复生成待收集阳光
- stats 统计口径（累计天数、每日阳光、连续天数）
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SASession

from app.auth import create_access_token, hash_password
from app.database import Base, engine
from app.main import app
from app.models import CheckIn, PendingSunlight, User

PARENT = 'streak_parent'
CHILD = 'streak_child'
PASSWORD = 'pw123456'


@pytest.fixture(scope='module')
def client():
    Base.metadata.create_all(bind=engine)
    with SASession(engine) as s:
        parent = s.query(User).filter(User.login_name == PARENT).first()
        if not parent:
            parent = User(
                name='连续打卡家长', login_name=PARENT, role='parent',
                password_hash=hash_password(PASSWORD), grade=0, is_onboarded=True,
            )
            s.add(parent)
            s.commit()
            s.refresh(parent)
        child = s.query(User).filter(User.login_name == CHILD).first()
        if not child:
            child = User(
                name='连续打卡孩子', login_name=CHILD, role='child',
                password_hash=hash_password(PASSWORD), grade=3,
                fk_users_parent=parent.pk_users, is_onboarded=True,
            )
            s.add(child)
            s.commit()
            s.refresh(child)
        ids = {'parent': parent.pk_users, 'child': child.pk_users}

    c = TestClient(app)
    c.headers.update({'Authorization': f'Bearer {create_access_token(ids["child"], "child")}'})
    c.parent_headers = {'Authorization': f'Bearer {create_access_token(ids["parent"], "parent")}'}
    c.child_id = ids['child']
    c.parent_id = ids['parent']
    yield c

    # 清理本次测试产生的打卡与阳光数据，保证可重复运行
    with SASession(engine) as s:
        s.query(PendingSunlight).filter(PendingSunlight.fk_users == ids['child']).delete()
        s.query(CheckIn).filter(CheckIn.fk_users == ids['child']).delete()
        s.commit()


def _submit(client, d: date, points: int = 10):
    return client.post(
        '/api/v1/checkins/',
        params={'check_date': d.isoformat(), 'total_points': points},
    )


def test_reject_future_date(client):
    future = date.today() + timedelta(days=3)
    resp = _submit(client, future)
    assert resp.status_code == 400
    assert '未来' in resp.json()['detail']


def test_submit_returns_streak_and_approve_generates_pending(client):
    today = date.today()
    resp = _submit(client, today, 12)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload['streak']['days'] == 1
    assert payload['streak']['isNewToday'] is True
    checkin_id = payload['checkin']['id']

    approved = client.post(f'/api/v1/checkins/{checkin_id}/approve', headers=client.parent_headers)
    assert approved.status_code == 200
    body = approved.json()
    assert body['streakDays'] == 1
    assert body['awarded'] == 12

    # 重复审批应被拒绝，且不会生成第二条待收集阳光
    again = client.post(f'/api/v1/checkins/{checkin_id}/approve', headers=client.parent_headers)
    assert again.status_code == 400
    with SASession(engine) as s:
        count = s.query(PendingSunlight).filter(
            PendingSunlight.fk_check_ins == checkin_id
        ).count()
    assert count == 1


def test_backfill_old_date_does_not_reset_streak(client):
    """补打卡历史日期后，连续天数仍以今天为锚点，不应被覆盖成 1。"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    resp = _submit(client, yesterday, 8)
    checkin_id = resp.json()['checkin']['id']
    client.post(f'/api/v1/checkins/{checkin_id}/approve', headers=client.parent_headers)

    with SASession(engine) as s:
        child = s.query(User).filter(User.pk_users == client.child_id).first()
        assert child.streak_days == 2

    # 补一条很久以前的打卡（中间断档），审批后连击不应被改成 1
    old = today - timedelta(days=20)
    old_id = _submit(client, old, 5).json()['checkin']['id']
    client.post(f'/api/v1/checkins/{old_id}/approve', headers=client.parent_headers)
    with SASession(engine) as s:
        child = s.query(User).filter(User.pk_users == client.child_id).first()
        assert child.streak_days == 2


def test_stats_endpoint(client):
    resp = client.get('/api/v1/checkins/stats', params={'days': 30})
    assert resp.status_code == 200
    data = resp.json()
    assert data['todayStatus'] == 'approved'
    assert data['totalDays'] >= 3
    assert data['streakDays'] == 2
    assert data['bestStreakDays'] >= 2
    assert len(data['daily']) == 30
    assert len(data['monthly']) == 6
    today_cell = data['daily'][-1]
    assert today_cell['date'] == date.today().isoformat()
    assert today_cell['status'] == 'approved'
    assert today_cell['points'] == 12
    assert data['totalSunlight'] >= 25


def test_child_cannot_read_other_child_stats(client):
    resp = client.get('/api/v1/checkins/stats', params={'child_id': client.parent_id})
    assert resp.status_code == 403
