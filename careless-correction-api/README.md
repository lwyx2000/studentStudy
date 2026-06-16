# 小树成长岛 - 后端 API (Python)

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库连接和 JWT 密钥

# 3. 创建数据库
mysql -u root -p -e "CREATE DATABASE careless_correction CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 执行数据库迁移
python src/migrations/run-mysql.py    # 或用: python -m app.migrations.run_mysql

# 5. 启动开发服务器
uvicorn app.main:app --reload --port 3001
```

## 目录结构

```
app/
├── main.py              # FastAPI 应用入口
├── config.py            # 环境配置
├── database.py          # SQLAlchemy 引擎
├── auth.py              # JWT 认证
├── models.py            # ORM 模型 (26 张表)
├── schemas.py           # Pydantic 响应模型
├── routers/             # 12 组 API 路由
│   ├── auth.py
│   ├── tasks.py
│   ├── habits.py
│   ├── mistakes.py
│   ├── items.py
│   ├── points.py
│   ├── badges.py
│   ├── covenants.py
│   ├── growth.py
│   ├── llm.py
│   ├── parent.py
│   └── community.py
└── services/
    ├── llm.py           # LLM API 调用
    └── growth.py        # 评估报告生成
migrations/
├── 001_init_mysql.sql   # MySQL 建表脚本 (26 张表)
└── run-mysql.py         # MySQL 迁移运行器
uploads/                 # 上传文件存储
```

## 技术栈

- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL 8.0+
- **认证**: JWT (python-jose)
- **LLM**: httpx (OpenAI 兼容接口)

## API 文档

启动后访问: http://localhost:3001/docs (Swagger UI)

## 数据库迁移

```bash
# 方式一: 直接执行 SQL
mysql -u root -p careless_correction < migrations/001_init_mysql.sql

# 方式二: 使用迁移脚本
python migrations/run-mysql.py
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 服务端口 | 3001 |
| DATABASE_URL | MySQL 连接串 | mysql+pymysql://root:root@localhost:3306/careless_correction |
| JWT_SECRET | JWT 签名密钥 | (必填) |
| UPLOAD_DIR | 上传文件目录 | ./uploads |
| LLM_ENDPOINT | LLM API 地址 | https://api.openai.com/v1 |
| LLM_API_KEY | LLM API 密钥 | (可选) |
| LLM_MODEL | LLM 模型名 | gpt-4o-mini |
