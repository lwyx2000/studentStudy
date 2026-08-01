# 小树成长岛 - 后端 API 接口文档

> 版本: v2.1 | 数据库: SQLite | 认证: JWT

---

## 一、API 路由总览（13 组）

### 认证与用户

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册（name + password） |
| POST | `/api/v1/auth/login` | 登录（家长用 name，孩子用 login_name） |
| POST | `/api/v1/auth/child-login` | 家长端切换孩子视角 |
| GET | `/api/v1/auth/session` | 获取当前用户信息 |
| PUT | `/api/v1/auth/profile` | 更新个人信息（name/grade/avatar_url） |
| PUT | `/api/v1/auth/password` | 修改密码（old_password + new_password） |

### 孩子管理（仅家长）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/children/` | 获取孩子列表 |
| POST | `/api/v1/children/` | 添加孩子 |
| PUT | `/api/v1/children/{child_id}` | 更新孩子信息 |
| DELETE | `/api/v1/children/{child_id}` | 删除孩子 |
| POST | `/api/v1/children/{child_id}/switch-token` | 获取孩子视角 token |

### 任务打卡（15 个端点，含子任务）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/tasks/today` | 获取今日任务列表（含子任务） |
| GET | `/api/v1/tasks/inventory` | 获取任务清单（含已归档） |
| GET | `/api/v1/tasks/{task_id}` | 获取单任务详情 |
| POST | `/api/v1/tasks/` | 创建任务 |
| PUT | `/api/v1/tasks/{task_id}` | 更新任务 |
| DELETE | `/api/v1/tasks/{task_id}` | 软删除任务 |
| DELETE | `/api/v1/tasks/{task_id}/permanent` | 永久删除任务 |
| POST | `/api/v1/tasks/{task_id}/complete` | 完成任务（返回获得阳光值） |
| POST | `/api/v1/tasks/checkin` | 拍照打卡（返回识别结果） |
| GET | `/api/v1/tasks/checkin/history` | 打卡历史记录 |
| POST | `/api/v1/tasks/scan` | 扫描单张图片 |
| POST | `/api/v1/tasks/scan/batch` | 批量扫描（返回 batchId） |
| GET | `/api/v1/tasks/scan/batch/{batch_id}` | 查询批量扫描状态 |
| GET | `/api/v1/tasks/subtasks/library` | 子任务库列表 |

**子任务**（一个任务可含多个子任务，区分平时/周末）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tasks/{task_id}/subtasks` | 添加子任务 |
| PUT | `/api/v1/tasks/{task_id}/subtasks/{subtask_id}` | 更新子任务 |
| DELETE | `/api/v1/tasks/{task_id}/subtasks/{subtask_id}` | 删除子任务 |

### 习惯 SOP（8 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/habits/` | 获取活跃习惯列表（支持 child_id） |
| GET | `/api/v1/habits/inventory` | 获取所有习惯（含 inactive） |
| GET | `/api/v1/habits/{habit_id}` | 获取单个习惯详情 |
| POST | `/api/v1/habits/` | 创建习惯 |
| PUT | `/api/v1/habits/{habit_id}` | 更新习惯 |
| DELETE | `/api/v1/habits/{habit_id}` | 软删除习惯 |
| DELETE | `/api/v1/habits/{habit_id}/permanent` | 永久删除习惯 |
| GET | `/api/v1/habits/steps/library` | 步骤库列表 |

### 错题（5 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/mistakes/upload` | 拍照上传错题图片（返回 URL） |
| POST | `/api/v1/mistakes/` | 创建错题记录 |
| GET | `/api/v1/mistakes/` | 错题列表（支持 child_id） |
| DELETE | `/api/v1/mistakes/{record_id}` | 删除错题 |
| GET | `/api/v1/mistakes/analysis` | LLM 分析统计 |

### 物品管理（7 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/items/loss` | 丢失记录列表 |
| POST | `/api/v1/items/loss` | 上报丢失 |
| DELETE | `/api/v1/items/loss/{record_id}` | 删除丢失记录 |
| GET | `/api/v1/items/stats` | 丢失统计 |
| GET | `/api/v1/items/storage` | 收纳记录列表 |
| POST | `/api/v1/items/storage` | 添加收纳记录 |
| DELETE | `/api/v1/items/storage/{record_id}` | 删除收纳记录 |

### 阳光值（11 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/points/balance` | 查询当前阳光值 |
| GET | `/api/v1/points/history` | 阳光值增减记录 |
| POST | `/api/v1/points/award` | 发放阳光值（amount + reason） |
| POST | `/api/v1/points/redeem` | 兑换物品 |
| GET | `/api/v1/points/rewards` | 可兑换物品列表 |
| POST | `/api/v1/points/rewards` | 添加兑换物品（家长） |
| PUT | `/api/v1/points/rewards/{reward_id}` | 更新兑换物品 |
| DELETE | `/api/v1/points/rewards/{reward_id}` | 删除兑换物品 |
| GET | `/api/v1/points/apples` | 查询苹果数量和苹果历史（含 sunlightPerApple） |
| POST | `/api/v1/points/apples/grow` | 用阳光值种出苹果（100 阳光 = 1 苹果） |
| POST | `/api/v1/points/apples/redeem` | 兑换苹果为现金（1 苹果 = 1 元，count + reason） |

### 勋章（4 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/badges/` | 勋章列表（支持 child_id，含进度） |
| POST | `/api/v1/badges/{badge_id}/unlock` | 手动解锁勋章 |
| POST | `/api/v1/badges/check-unlocks` | 检查并自动解锁达标勋章 |
| — | 启动种子数据 | 首次启动自动初始化勋章定义 |

### 打卡审批（4 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/checkins/` | 提交打卡记录 |
| GET | `/api/v1/checkins/pending` | 获取待审批列表（家长） |
| POST | `/api/v1/checkins/{checkin_id}/approve` | 审批通过（发放阳光值） |
| POST | `/api/v1/checkins/{checkin_id}/reject` | 审批拒绝 |

### 成长评估（LLM 驱动，4 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/growth/assessment` | 触发一次 LLM 综合评估 |
| GET | `/api/v1/growth/trend` | 获取成长趋势数据 |
| GET | `/api/v1/growth/report` | 获取评估报告 |
| GET | `/api/v1/growth/alerts` | 获取预警 |

### LLM 配置（3 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/llm/config` | 获取 LLM 配置 |
| PUT | `/api/v1/llm/config` | 更新 LLM 配置 |
| POST | `/api/v1/llm/test` | 测试 LLM 连接 |

### 家长设置（2 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/parent/settings` | 获取家长设置 |
| PUT | `/api/v1/parent/settings` | 更新家长设置 |

### 文章资源（2 个端点）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/articles` | 文章列表（支持 category 筛选） |
| GET | `/api/v1/articles/suggested` | 推荐文章 |

---

## 二、通用参数说明

### child_id 参数

支持 `child_id` 的端点（家长端调用时）：
- 家长端 API 默认操作当前选中的孩子
- 传 `child_id` 可指定操作特定孩子
- 孩子角色调用时 child_id 参数无效

---

## 三、手机端方案（仅孩子使用）

当前项目为 Vue 3 SPA，支持移动端响应式布局。手机端核心功能：

### 首页 — 今日任务
- 展示 `GET /api/v1/tasks/today` 返回的任务列表
- 任务卡片：图标、标题、说明、阳光值奖励
- 点击「拍照打卡」→ 调起相机/相册 → 上传到 `POST /api/v1/tasks/checkin`
- 后端返回识别结果，标记完成，增加阳光值

### 阳光值页面
- 查询余额（`GET /api/v1/points/balance`）
- 历史记录（`GET /api/v1/points/history`）

### 勋章页面
- 勋章列表（`GET /api/v1/badges/`）
- 已解锁/未解锁状态展示

---

## 四、家长端 LLM 配置

### 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API 地址 | LLM 服务 endpoint | `https://api.openai.com/v1` |
| API Key | 认证密钥 | 空 |
| 模型 | 模型名称 | `gpt-4o-mini` |
| 错题分析 Prompt | 错题图片分析提示词 | 见代码 |
| 成长评估 Prompt | 综合评估提示词 | 见代码 |
| 评估周期 | daily / weekly / monthly | weekly |
| 启用状态 | 开关 | 关 |

### LLM 调用场景

| 场景 | 输入 | 输出 |
|------|------|------|
| 拍照打卡识别 | 任务图片 | 完成/未完成 |
| 错题分析 | 错题图片+科目 | 粗心类型、知识薄弱点、建议 |
| 成长评估 | 错题数据+完成率+丢失率 | 评估报告、预警、建议 |
