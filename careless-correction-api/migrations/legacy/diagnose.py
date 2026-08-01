"""
全面诊断：检查数据库结构、数据和后端查询
运行: python migrations/legacy/diagnose.py
"""
import sqlite3
import os
import sys
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'app.db')

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在: {db_path}")
    sys.exit(1)

print(f"📁 数据库: {db_path}")
print(f"📏 大小: {os.path.getsize(db_path)} bytes")
print(f"🕐 修改时间: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
print()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 1. 列出所有表
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in c.fetchall()]
print(f"📋 所有表 ({len(tables)}): {tables}")
print()

# 2. 检查每个表的结构
for table in tables:
    c.execute(f"PRAGMA table_info({table})")
    cols = [(row[1], row[2], row[4] if row[4] is not None else '') for row in c.fetchall()]
    print(f"  表 {table}:")
    for name, dtype, default in cols:
        print(f"    - {name} ({dtype}) 默认={default}")
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"    => {count} 条记录")
    if count > 0:
        c.execute(f"SELECT * FROM {table} LIMIT 3")
        for row in c.fetchall():
            print(f"      示例: {dict(row)}")
    print()

# 3. 特别关注用户、习惯、任务
print("=" * 60)
print("🔍 重点检查")
print("=" * 60)

# 用户
c.execute("SELECT pk_users, name, role, fk_users_parent FROM t_users")
users = c.fetchall()
print(f"\n用户 ({len(users)}):")
for u in users:
    print(f"  ID={u['pk_users']}, 名字={u['name']}, 角色={u['role']}, 家长ID={u['fk_users_parent']}")

# 习惯
c.execute("SELECT * FROM t_habit_sops")
habits = c.fetchall()
print(f"\n习惯 ({len(habits)}):")
for h in habits:
    d = dict(h)
    print(f"  {d}")

# 任务
c.execute("SELECT * FROM t_tasks")
tasks = c.fetchall()
print(f"\n任务 ({len(tasks)}):")
for t in tasks:
    d = dict(t)
    print(f"  {d}")

# 4. 模拟查询
print("\n" + "=" * 60)
print("🔍 模拟后端查询")
print("=" * 60)

# 查询习惯 - 检查是否有 active=1 的过滤
user_id = None
c.execute("SELECT pk_users FROM t_users WHERE role='child' LIMIT 1")
row = c.fetchone()
if row:
    user_id = row['pk_users']
    print(f"\n子用户 ID: {user_id}")

    # 查询活跃习惯
    try:
        c.execute("SELECT * FROM t_habit_sops WHERE fk_users=? AND active=1", (user_id,))
        active_habits = c.fetchall()
        print(f"  GET /habits/ (active=1): {len(active_habits)} 条")
        for h in active_habits:
            print(f"    - {dict(h)}")
    except Exception as e:
        print(f"  ❌ GET /habits/ 查询失败: {e}")
    
    # 查询全部习惯
    try:
        c.execute("SELECT * FROM t_habit_sops WHERE fk_users=?", (user_id,))
        all_habits = c.fetchall()
        print(f"  GET /habits/inventory (全部): {len(all_habits)} 条")
        for h in all_habits:
            print(f"    - {dict(h)}")
    except Exception as e:
        print(f"  ❌ GET /habits/inventory 查询失败: {e}")

    # 查询活跃的待完成任务
    try:
        c.execute("SELECT * FROM t_tasks WHERE fk_users=? AND active=1 AND status='pending'", (user_id,))
        active_tasks = c.fetchall()
        print(f"\n  GET /tasks/today (active=1, status=pending): {len(active_tasks)} 条")
        for t in active_tasks:
            print(f"    - {dict(t)}")
    except Exception as e:
        print(f"  ❌ GET /tasks/today 查询失败: {e}")

    # 查询全部任务
    try:
        c.execute("SELECT * FROM t_tasks WHERE fk_users=?", (user_id,))
        all_tasks = c.fetchall()
        print(f"  GET /tasks/inventory (全部): {len(all_tasks)} 条")
        for t in all_tasks:
            print(f"    - {dict(t)}")
    except Exception as e:
        print(f"  ❌ GET /tasks/inventory 查询失败: {e}")

conn.close()
print("\n✅ 诊断完成")
