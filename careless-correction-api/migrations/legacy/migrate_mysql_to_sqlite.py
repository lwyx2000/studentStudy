"""
MySQL → SQLite 数据迁移脚本
将原 MySQL 数据库中的所有数据导入到本地 SQLite 数据库中。

用法: python migrations/legacy/migrate_mysql_to_sqlite.py
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pymysql
from sqlalchemy import create_engine, event, inspect, text, MetaData

from app.config.database import db_config

# ===== MySQL 连接配置（原数据库） =====
MYSQL_CONFIG = {
    'host': '10.100.213.248',
    'port': 3306,
    'user': 'sosdb',
    'password': 'sosdb!@#',
    'database': 'careless_correction',
    'charset': 'utf8mb4',
}

# 按照外键依赖顺序排列的表（父表在前）
TABLE_ORDER = [
    't_users',
    't_assessments',
    't_habit_sops',
    't_sop_steps',
    't_tasks',
    't_sub_tasks',
    't_mistake_records',
    't_mistake_reviews',
    't_item_storage_records',
    't_item_loss_records',
    't_reward_items',
    't_sunlight_history',
    't_check_ins',
    't_llm_config',
    't_growth_snapshots',
    't_diagnostic_alerts',
    't_badges',
    't_badge_unlocks',
    't_parent_settings',
    't_articles',
    't_article_bookmarks',
    't_growth_reports',
    't_task_weekly_progress',
]


def get_mysql_connection():
    """建立 MySQL 连接"""
    return pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)


def get_sqlite_engine():
    """创建 SQLite 引擎"""
    engine = create_engine(
        db_config.url,
        echo=False,
        connect_args={'check_same_thread': False},
    )
    return engine


def get_mysql_tables(cursor):
    """获取 MySQL 中实际存在的表名"""
    cursor.execute("SHOW TABLES")
    rows = cursor.fetchall()
    # SHOW TABLES 返回的 key 是 'Tables_in_<dbname>'
    tables = set()
    for row in rows:
        tables.add(list(row.values())[0])
    return tables


def get_table_columns(cursor, table_name):
    """获取 MySQL 表的列名"""
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    rows = cursor.fetchall()
    return [row['Field'] for row in rows]


def migrate_table(cursor, sqlite_conn, table_name, sqlite_columns):
    """迁移单张表的数据"""
    # 获取 MySQL 表的列
    mysql_columns = get_table_columns(cursor, table_name)

    # 取交集：只迁移两边都有的列
    common_columns = [col for col in mysql_columns if col in sqlite_columns]

    if not common_columns:
        print(f"  [跳过] {table_name}: 无公共列")
        return 0

    # 读取 MySQL 数据
    cols_str = ', '.join(f'`{c}`' for c in common_columns)
    cursor.execute(f"SELECT {cols_str} FROM `{table_name}`")
    rows = cursor.fetchall()

    if not rows:
        print(f"  [空表] {table_name}: 0 行")
        return 0

    # 构建 INSERT 语句（列名用双引号包裹，避免 SQLite 保留字冲突）
    quoted_cols = ', '.join(f'"{c}"' for c in common_columns)
    placeholders = ', '.join(f':{c}' for c in common_columns)
    insert_sql = text(
        f'INSERT INTO {table_name} ({quoted_cols}) VALUES ({placeholders})'
    )

    # 处理数据类型转换
    cleaned_rows = []
    for row in rows:
        cleaned = {}
        for col in common_columns:
            val = row[col]
            # bytes → str (MySQL JSON 字段可能返回 bytes)
            if isinstance(val, bytes):
                val = val.decode('utf-8')
            cleaned[col] = val
        cleaned_rows.append(cleaned)

    # 批量插入
    sqlite_conn.execute(insert_sql, cleaned_rows)
    return len(cleaned_rows)


def main():
    print("=" * 60)
    print("MySQL → SQLite 数据迁移")
    print(f"MySQL: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}")
    print(f"SQLite: {db_config.db_path}")
    print("=" * 60)

    # 1. 连接 MySQL
    print("\n[1] 连接 MySQL...")
    try:
        mysql_conn = get_mysql_connection()
        cursor = mysql_conn.cursor()
        print("    MySQL 连接成功")
    except Exception as e:
        print(f"    MySQL 连接失败: {e}")
        sys.exit(1)

    # 2. 准备 SQLite
    print("\n[2] 准备 SQLite...")
    sqlite_engine = get_sqlite_engine()

    # 确保表已创建
    from app.database import Base
    from app import models  # noqa: F401 确保所有模型被加载
    Base.metadata.create_all(bind=sqlite_engine)
    print("    SQLite 表结构就绪")

    # 3. 获取 MySQL 中实际存在的表
    mysql_tables = get_mysql_tables(cursor)
    print(f"\n[3] MySQL 中共有 {len(mysql_tables)} 张表")

    # 4. 获取 SQLite 表的列信息
    inspector = inspect(sqlite_engine)
    sqlite_table_columns = {}
    for table_name in inspector.get_table_names():
        sqlite_table_columns[table_name] = [c['name'] for c in inspector.get_columns(table_name)]

    # 5. 按顺序迁移数据
    print("\n[4] 开始迁移数据...")
    total_rows = 0

    with sqlite_engine.connect() as sqlite_conn:
        # 暂时禁用外键约束
        sqlite_conn.execute(text("PRAGMA foreign_keys=OFF"))

        for table_name in TABLE_ORDER:
            if table_name not in mysql_tables:
                print(f"  [跳过] {table_name}: MySQL 中不存在")
                continue
            if table_name not in sqlite_table_columns:
                print(f"  [跳过] {table_name}: SQLite 中不存在")
                continue

            try:
                count = migrate_table(cursor, sqlite_conn, table_name, sqlite_table_columns[table_name])
                total_rows += count
                if count > 0:
                    print(f"  [完成] {table_name}: {count} 行")
            except Exception as e:
                print(f"  [错误] {table_name}: {e}")

        sqlite_conn.commit()

        # 恢复外键约束
        sqlite_conn.execute(text("PRAGMA foreign_keys=ON"))

    # 6. 检查是否有遗漏的表
    missed = mysql_tables - set(TABLE_ORDER)
    if missed:
        print(f"\n[5] MySQL 中还有未迁移的表: {missed}")

    # 7. 关闭连接
    mysql_conn.close()

    print(f"\n{'=' * 60}")
    print(f"迁移完成！共导入 {total_rows} 行数据到 SQLite")
    print(f"数据库文件: {db_config.db_path}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
