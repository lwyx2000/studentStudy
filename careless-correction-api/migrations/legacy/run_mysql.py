"""
MySQL 数据库迁移脚本

用法：
    python migrations/legacy/run_mysql.py

依赖 .env 中的 DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME 配置
"""

import os
import sys

import pymysql

# 尝试加载 .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.isfile(dotenv_path):
    with open(dotenv_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            os.environ.setdefault(key.strip(), val.strip())


def run():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root'),
        'database': os.getenv('DB_NAME', 'careless_correction'),
    }

    print(f'连接数据库: {db_config["host"]}:{db_config["port"]}/{db_config["database"]}')

    connection = pymysql.connect(**db_config, charset='utf8mb4')
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{db_config["database"]}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            cursor.execute(f'USE `{db_config["database"]}`')

        sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '001_init_mysql.sql')
        with open(sql_path, encoding='utf-8') as f:
            sql = f.read()

        statements = [
            s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')
        ]

        with connection.cursor() as cursor:
            for stmt in statements:
                cursor.execute(stmt)

        connection.commit()
        print(f'迁移完成: 共执行 {len(statements)} 条 SQL 语句')
    except Exception as e:
        connection.rollback()
        print(f'迁移失败: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == '__main__':
    run()
