# 小树成长岛 - 后端 API (Python)

> 基于 FastAPI + SQLite 的 RESTful API，支持亲子协同的儿童粗心矫正系统。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（可选）
cp .env.example .env
# 默认使用 SQLite，无需额外配置

# 3. 启动开发服务器（自动创建数据库和表）
uvicorn app.main:app --reload --port 3001

# 4. 访问 API 文档
# http://localhost:3001/docs
```

## 目录结构

```
app/
├── main.py                    # FastAPI 应用入口 + 路由注册
├── config/
│   └── database.py            # 数据库配置（SQLite）
├── config.py                  # 应用设置（已废弃，保留兼容）
├── database.py                # SQLAlchemy 引擎 + 会话管理
├── auth.py                    # JWT 认证依赖
├── models.py                  # ORM 模型 (24 张表)
├── schemas.py                 # Pydantic 响应模型
├── routers/                   # 13 组 API 路由
│   ├── auth.py                # 认证（6 端点）
│   ├── children.py            # 孩子管理（5 端点）
│   ├── tasks.py               # 任务（15 端点，含子任务）
│   ├── habits.py              # 习惯 SOP（8 端点）
│   ├── mistakes.py            # 错题（5 端点）
│   ├── items.py               # 物品（7 端点）
│   ├── points.py              # 阳光值（8 端点）
│   ├── badges.py              # 勋章（2 端点）
│   ├── checkins.py            # 打卡审批（4 端点）
│   ├── growth.py              # 成长评估（4 端点）
│   ├── llm.py                 # LLM 配置（3 端点）
│   ├── parent.py              # 家长设置（2 端点）
│   └── articles.py            # 文章资源（2 端点）
└── services/
    ├── llm.py                 # LLM API 调用
    └── growth.py              # 评估报告生成
migrations/                    # 历史 MySQL 迁移 SQL 文件（Python 脚本见 legacy/）
├── 001_init_mysql.sql
├── 002_add_password_hash.sql
├── 003_add_login_name.sql
├── 004_add_sub_tasks.sql
├── 005_add_apples_field.sql
└── legacy/                    # 一次性修复/迁移脚本（历史归档）
    ├── diagnose.py
    ├── fix_active_column.py
    ├── fix_missing_columns.py
    ├── migrate_mysql_to_sqlite.py
    └── run_mysql.py
uploads/                       # 上传文件存储
```

## 技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **SQLAlchemy 2.0** | ORM |
| **SQLite** | 数据库（本地存储） |
| **JWT (python-jose)** | 认证 |
| **httpx** | LLM API 调用 |
| **python-multipart** | 文件上传解析 |

## API 文档

启动后访问: http://localhost:3001/docs (Swagger UI)

## 数据库

- 使用 **SQLite** 作为本地数据库
- 数据库文件默认存储在 `data/app.db`
- 启动时自动创建表和目录
- 支持自动迁移（基于 SQLAlchemy ORM）

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 服务端口 | 3001 |
| DB_PATH | SQLite 数据库路径 | ./data/app.db |
| JWT_SECRET | JWT 签名密钥 | dev-secret-change-in-production |
| UPLOAD_DIR | 上传文件目录 | ./uploads |