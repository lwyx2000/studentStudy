

---

# 小树成长岛 - 全小学阶段儿童成长系统

> 基于执行功能训练的亲子协同成长平台，帮助 1-6 年级儿童建立良好习惯、减少粗心错误、培养自我管理能力。


## 项目概览

| 模块 | 技术栈 | 说明 |
|------|--------|------|
| **前端** | Vue 3 + TypeScript + Vite + Pinia + Vue Router | 亲子双端 SPA |
| **后端** | Python FastAPI + SQLAlchemy 2.0 + SQLite | RESTful API |
| **认证** | JWT (python-jose) | 家长/孩子角色分离 |

---

## 系统页面地图

### 孩子端

| 路由 | 页面 | 功能 |
|------|------|------|
| /login | 登录注册 | 家长/孩子登录注册 |
| /onboarding | 执行功能基线评估 | 5 维量表评估，生成初始难度等级 |
| /dashboard | 亲子协同仪表盘 | 今日任务卡片 + 阳光值 + 勋章入口 |
| /habit | 每日微习惯打卡 | SOP 步骤展示 + A4 打印清单 |
| /mistake | 智能错题本 | 拍照上传 + 题库列表 |
| /tracker | 物品追踪实验室 | 丢失记录 + 收纳记录双列表 |
| /growth | 成长档案与预警 | 趋势图 + 智能预警卡片 |
| /badge | 勋章馆 | 勋章墙展示与自动解锁 |
| /sunlight | 阳光值兑换 | 阳光值余额 + 兑换商城 |
| /tree | 阳光树 | 阳光值可视化（苹果树隐喻） |

### 家长端

| 路由 | 页面 | 功能 |
|------|------|------|
| /parent | 家长控制中心 | 家长端总览仪表盘 |
| /parent/children | 孩子管理 | 添加/编辑/删除孩子账号 |
| /parent/tasks | 任务习惯管理 | 创建/编辑任务和习惯，含子任务管理 |
| /parent/habit-assign | 习惯布置 | 为孩子布置每周核心习惯（SOP 步骤 + 奖励） |
| /parent/progress | 进度看板 | 孩子多维进度数据可视化 |
| /parent/items | 物品统计 | 物品丢失数据统计 |
| /parent/sunlight | 阳光值管理 | 阳光值发放与兑换管理 |
| /parent/badges | 勋章管理 | 勋章列表与配置 |
| /parent/llm | LLM 模型配置 | 对接 AI 分析的模型参数配置 |
| /parent/inventory | 任务习惯清单 | 查看所有（含已归档）任务与习惯 |

---

## 核心功能模块

### 1. 注册与基线评估 (/onboarding)
- 物理年级选择 + 5 项执行功能量表（专注持久度、物品整洁度、情绪克制力、计划启动力、冲动抑制力）
- 自动计算推荐难度等级（1-5 级）
- 双轨输入：家长可同时为多个孩子评估

### 2. 亲子仪表盘 (/dashboard)
- 今日任务卡片列表（带完成状态和阳光值奖励）
- 阳光值余额 + 勋章入口
- 每周进度概览

### 3. 习惯打卡 (/habit)
- 习惯 SOP 步骤展示（多步骤引导）
- **A4 打印清单**：选择今日任务，一键打印纸质打卡单
- 拍照回传核销（AI 识别手写痕迹）

### 4. 错题本 (/mistake)
- 拍照上传错题图片
- 错题列表浏览
- 12 类粗心分类标记
- 间隔复习提醒

### 5. 物品追踪 (/tracker)
- **丢失记录列表**：物品名、丢失地点、估计金额、丢失频率
- **收纳记录列表**：物品名、收纳位置、备注
- 高频丢失自动预警（30 天内 >= 3 次触发红光提醒）
- 丢失累计账单统计

### 6. 成长档案 (/growth)
- 错题率 / 物品丢失率 / 任务完成率趋势图
- 智能预警卡片（非焦虑设计：阶段性发展发现）
- LLM 驱动的综合评估报告

### 7. 勋章馆 (/badge)
- 勋章解锁墙（彩色纸屑动效）
- 解锁条件：连续打卡天数 / 任务完成数 / 零物品丢失周期

### 8. 阳光值兑换 (/sunlight)
- 阳光值余额展示
- 兑换商城（家长配置兑换物品）
- 阳光树：每 100 阳光值 = 1 个苹果

### 9. 阳光树 (/tree)
- 阳光值可视化展示
- 苹果树成长隐喻（阳光值 -> 苹果 -> 实物奖励）

---

## 技术架构

### 前端 (Vue 3)

```
src/
├── App.vue                    # 根组件
├── main.ts                    # 入口
├── style.css                  # 全局样式
├── router/index.ts            # 路由配置（19 条路由）
├── stores/index.ts            # Pinia 状态管理
│   ├── useUserStore           # 用户 + 阳光值 + 评估
│   ├── useTaskStore           # 任务 + 习惯
│   ├── useMistakeStore        # 错题
│   ├── useGrowthStore         # 成长数据 + 物品追踪
│   ├── useBadgeStore          # 勋章
│   ├── useChildSelectStore    # 孩子选择（家长端）
│   └── useParentStore         # 家长设置 + LLM + 文章资源
├── utils/
│   ├── api.ts                 # API 调用 + 数据规范化
│   └── constants.ts           # 常量（分类、年级等）
├── components/                # 复用组件
│   ├── MainLayout.vue
│   ├── ChildSelector.vue
│   ├── WeekdayPicker.vue
│   └── InventoryPickerModal.vue
├── views/
│   ├── LoginRegister.vue      # 登录注册
│   └── child/                 # 孩子端（9 个页面）
│       ├── Dashboard.vue
│       ├── OnboardingAssessment.vue
│       ├── HabitPrintableCenter.vue
│       ├── DiagnosticMistakeBook.vue
│       ├── ItemTracker.vue
│       ├── GrowthArchive.vue
│       ├── BadgeRoom.vue
│       ├── SunlightRedemption.vue
│       └── SunshineTree.vue
│   └── parent/                # 家长端（9 个页面）
│       ├── ChildManagement.vue
│       ├── ItemStats.vue
│       ├── LlmConfig.vue
│       ├── ParentBadges.vue
│       ├── ParentalControlCenter.vue
│       ├── ProgressDashboard.vue
│       ├── SunlightManagement.vue
│       ├── TaskHabitManager.vue
│       └── TaskHabitInventory.vue
```

### 后端 API (FastAPI)

```
app/
├── main.py                    # 应用入口 + 路由注册
├── config/database.py         # 数据库配置（SQLite）
├── database.py                # SQLAlchemy 引擎 + 会话
├── models.py                  # ORM 模型（24 张表）
├── schemas.py                 # Pydantic 响应模型
├── auth.py                    # JWT 认证依赖
└── routers/                   # 13 组 API 路由
    ├── auth.py                # 认证（6 端点）
    ├── children.py            # 孩子管理（5 端点）
    ├── tasks.py               # 任务（15 端点，含子任务）
    ├── habits.py              # 习惯 SOP（8 端点）
    ├── mistakes.py            # 错题（5 端点）
    ├── items.py               # 物品（7 端点）
    ├── points.py              # 阳光值（8 端点）
    ├── badges.py              # 勋章（2 端点）
    ├── checkins.py            # 打卡审批（4 端点）
    ├── growth.py              # 成长评估（4 端点）
    ├── llm.py                 # LLM 配置（3 端点）
    ├── parent.py              # 家长设置（2 端点）
    └── articles.py            # 文章资源（2 端点）
```

### 数据库模型 (24 张表)

| 表名 | 说明 |
|------|------|
| t_users | 用户（家长/孩子） |
| t_assessments | 执行功能评估 |
| t_tasks | 每日任务 |
| t_sub_tasks | 子任务（区分平时/周末） |
| t_habit_sops | 习惯标准操作程序 |
| t_sop_steps | SOP 步骤 |
| t_mistake_records | 错题记录 |
| t_mistake_reviews | 错题复习记录 |
| t_item_loss_records | 物品丢失记录 |
| t_item_storage_records | 物品收纳记录 |
| t_reward_items | 阳光值兑换物品 |
| t_sunlight_history | 阳光值变动记录 |
| t_badges | 勋章定义 |
| t_badge_unlocks | 勋章解锁记录 |
| t_parent_settings | 家长设置 |
| t_growth_snapshots | 成长数据快照 |
| t_diagnostic_alerts | 诊断预警 |
| t_llm_config | LLM 配置 |
| t_check_ins | 打卡审批记录 |
| t_articles | 循证资源 |
| t_article_bookmarks | 文章收藏 |
| t_growth_reports | 成长报告 |
| t_task_weekly_progress | 每周打卡进度 |
| t_apple_history | 苹果变动记录 |

---

## 快速开始

### 后端

```bash
cd careless-correction-api

# 安装依赖
pip install -r requirements.txt

# 启动（自动创建 SQLite 数据库）
uvicorn app.main:app --reload --port 3001

# 访问 API 文档
# http://localhost:3001/docs
```

### 前端

```bash
cd careless-correction

# 安装依赖
npm install

# 开发模式
npm run dev
```

### 环境变量

后端 .env 配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 服务端口 | 3001 |
| DB_PATH | SQLite 数据库路径 | ./data/app.db |
| JWT_SECRET | JWT 密钥 | dev-secret-change-in-production |
| UPLOAD_DIR | 上传文件目录 | ./uploads |

---

## Docker 部署

支持 Jenkins 流水线自动部署或手动脚本部署，前后端通过 Docker 容器化发布到服务器（Nginx 反向代理 + FastAPI + Vue 构建产物 volume）。

```bash
# 方式一：Jenkins（推荐）—— 使用仓库根目录 Jenkinsfile 创建流水线任务
# 方式二：手动脚本
bash deploy.sh
```

详细说明（服务器准备、Jenkins 配置、参数含义、数据备份、FAQ）见 [docs/deploy.md](docs/deploy.md)。

---

## 设计特点

### 游戏化激励体系
- **阳光值**：完成任务、好习惯获得的积分
- **苹果树**：每 100 阳光值 = 1 个苹果，可兑换实物奖励
- **勋章系统**：连续打卡、零丢失周期等条件解锁

### 循证心理学埋点
- **非焦虑设计**：预警卡片使用积极而非消极的表达
- **防贿赂提示**：过度物质奖励自动提醒
- **正向反馈优先**：强调进步而非问题

### 双端协同
- 家长端：管理配置、数据看板、审批打卡
- 孩子端：任务执行、习惯养成、游戏化激励
- 家长可一键切换到孩子视角查看
