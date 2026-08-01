"""
检查并修复数据库中缺少的列（active 等）
运行: python migrations/legacy/fix_missing_columns.py
"""
import sqlite3
import os
import sys

# 数据库路径（相对于项目根目录）
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'app.db')

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在: {db_path}")
    sys.exit(1)

print(f"📁 数据库: {db_path}")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 所有需要检查的表和可能缺失的列
checks = {
    't_habit_sops': [
        ('active', 'BOOLEAN DEFAULT 1'),
    ],
    't_tasks': [
        ('active', 'BOOLEAN DEFAULT 1'),
    ],
    't_check_ins': [
        ('approved_at', 'DATETIME'),
    ],
}

for table, columns_to_add in checks.items():
    # 检查表是否存在
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not c.fetchone():
        print(f"  ⏭️  表 {table} 不存在，跳过")
        continue

    # 获取现有列
    c.execute(f"PRAGMA table_info({table})")
    existing_cols = {row[1] for row in c.fetchall()}
    print(f"\n📋 表 {table} 现有列: {sorted(existing_cols)}")

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            try:
                sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                c.execute(sql)
                print(f"  ✅ 添加列 {col_name} ({col_def}) → {table}")
            except Exception as e:
                print(f"  ❌ 添加列 {col_name} 失败: {e}")
        else:
            print(f"  ✅ 列 {col_name} 已存在")

# 验证数据
print("\n\n📊 数据验证:")
for table in ['t_habit_sops', 't_tasks']:
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"  {table}: {count} 条记录")

c.execute("SELECT pk_habit_sops, title, active FROM t_habit_sops LIMIT 10")
print("\n习惯列表:")
for row in c.fetchall():
    print(f"  ID={row[0]}, 标题={row[1]}, active={row[2]}")

c.execute("SELECT pk_tasks, title, active FROM t_tasks LIMIT 10")
print("\n任务列表:")
for row in c.fetchall():
    print(f"  ID={row[0]}, 标题={row[1]}, active={row[2]}")

conn.commit()
conn.close()
print("\n✅ 修复完成！请重启后端服务。")
