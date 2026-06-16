# 小树成长岛 - 后端 API 设计与手机端方案

---

## 一、后端 API 接口

### 认证与用户

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册（家长/孩子） |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/session` | 获取当前用户信息 |
| PUT | `/api/v1/auth/profile` | 更新个人信息 |

### 任务打卡

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/tasks/today` | 获取今日任务列表 |
| POST | `/api/v1/tasks/:id/complete` | 完成任务（返回获得阳光值） |
| POST | `/api/v1/tasks/checkin` | 手机拍照打卡（接收图片，返回识别结果） |
| GET | `/api/v1/tasks/checkin/history` | 打卡历史记录 |

### 习惯 SOP

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/habits/current` | 获取当前习惯 SOP |
| PUT | `/api/v1/habits/current` | 更新当前习惯（家长） |
| POST | `/api/v1/habits` | 创建新习惯（自动归档旧的） |
| GET | `/api/v1/habits/history` | 历史习惯列表 |

### 错题（拍照 + LLM 分析）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/mistakes/upload` | 拍照上传错题图片（返回图片 URL） |
| POST | `/api/v1/mistakes` | 创建错题记录（含 LLM 分析结果） |
| GET | `/api/v1/mistakes` | 错题列表 |
| DELETE | `/api/v1/mistakes/:id` | 删除错题 |
| GET | `/api/v1/mistakes/analysis` | LLM 分析统计（粗心类型分布、知识薄弱点） |

### 物品管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/items/loss` | 丢失记录列表 |
| POST | `/api/v1/items/loss` | 上报丢失 |
| GET | `/api/v1/items/stats` | 丢失统计（总成本、高频物品） |
| POST | `/api/v1/items/storage` | 添加收纳记录 |
| GET | `/api/v1/items/storage` | 收纳记录列表 |

### 阳光值

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/points/balance` | 查询当前阳光值 |
| GET | `/api/v1/points/history` | 阳光值增减记录 |
| POST | `/api/v1/points/redeem` | 兑换物品 |
| GET | `/api/v1/points/rewards` | 可兑换物品列表（家长配置） |
| POST | `/api/v1/points/rewards` | 添加兑换物品（家长） |
| PUT | `/api/v1/points/rewards/:id` | 更新兑换物品 |
| DELETE | `/api/v1/points/rewards/:id` | 删除兑换物品 |

### 勋章与契约

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/badges` | 勋章列表 |
| POST | `/api/v1/badges/:id/unlock` | 解锁勋章 |
| GET | `/api/v1/covenants` | 契约列表 |
| POST | `/api/v1/covenants` | 创建契约 |

### 成长评估（LLM 驱动）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/growth/assessment` | 触发一次 LLM 综合评估 |
| GET | `/api/v1/growth/trend` | 获取成长趋势数据 |
| GET | `/api/v1/growth/report` | 获取评估报告 |
| GET | `/api/v1/growth/alerts` | 获取预警 |

### LLM 配置（家长端）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/llm/config` | 获取 LLM 配置 |
| PUT | `/api/v1/llm/config` | 更新 LLM 配置 |
| POST | `/api/v1/llm/test` | 测试 LLM 连接 |

### 家长设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/parent/settings` | 获取家长设置 |
| PUT | `/api/v1/parent/settings` | 更新家长设置 |

### 社区

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/community/posts` | 帖子列表 |
| POST | `/api/v1/community/posts` | 发布帖子 |

---

## 二、手机端（仅孩子使用）

### 选型建议

**推荐：微信小程序**（拍照功能原生支持，开发成本最低）或 **Uniapp**（一套代码多端发布）。

### 页面结构

```
手机端首页（今日任务列表）
  ├── 任务卡片：标题 + 图标 + 完成状态
  ├── 拍照按钮 → 调起摄像头 / 相册
  └── 状态：已完成 / 待完成

底部 Tab 导航
  ├── 📋 任务（首页）
  ├── ☀️ 阳光值
  │   ├── 当前阳光值
  │   └── 兑换记录列表
  └── 🏅 勋章
      └── 勋章网格展示
```

### 页面功能详述

#### 1. 首页 — 今日任务

- 展示 `GET /api/v1/tasks/today` 返回的任务列表
- 每条任务卡片显示：图标、标题、说明、阳光值奖励
- 点击「拍照打卡」按钮 → 调起系统相机/相册 → 上传图片到 `POST /api/v1/tasks/checkin`
- 后端返回识别结果，前端标记为已完成，增加阳光值

#### 2. 阳光值页面

- 展示当前阳光值余额（`GET /api/v1/points/balance`）
- 展示兑换记录列表（`GET /api/v1/points/history`，过滤 `type=spend`）
- 只读，不能操作兑换

#### 3. 勋章页面

- 展示所有勋章（`GET /api/v1/badges`）
- 已解锁 / 未解锁状态展示
- 纯展示，不能操作

### 拍照打卡流程

```
1. 孩子点击任务卡片上的「拍照」按钮
2. 调起系统相机（或相册选择）
3. 上传图片到 POST /api/v1/tasks/checkin
4. 后端存储图片，调用 LLM 识别内容
5. 识别场景：
   - 「整理书包 3 分区」→ 识别书包分区是否清晰
   - 「舒尔特方格」→ 识别完成时间
   - 「指读任务」→ 确认书本和手指位置
6. 返回识别结果，标记任务完成，增加阳光值
```

---

## 三、家长端 LLM 配置页面

### 页面位置

家长导航新增：**🤖 模型配置**（路由 `/parent/llm`）

### 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API 地址 | LLM 服务 endpoint | `https://api.openai.com/v1` |
| API Key | 认证密钥 | 空（加密存储） |
| 模型 | 使用的模型名称 | `gpt-4o-mini` |
| 错题分析 Prompt | 分析错题图片的提示词 | 见下方 |
| 成长评估 Prompt | 综合评估的提示词 | 见下方 |
| 评估周期 | daily / weekly / monthly | weekly |
| 启用状态 | 开/关 | 关 |

### 数据结构

```typescript
export interface LlmConfig {
  endpoint: string
  apiKey: string
  model: string
  mistakePrompt: string
  assessmentPrompt: string
  assessmentCron: 'daily' | 'weekly' | 'monthly'
  enabled: boolean
}
```

### LLM 调用场景

| 场景 | 输入 | 输出 |
|------|------|------|
| 拍照打卡识别 | 任务图片 | 完成 / 未完成 |
| 错题分析 | 错题图片 + 科目 | 粗心类型、知识薄弱点、建议 |
| 成长评估 | 错题数据 + 任务完成率 + 丢失率 | 评估报告、预警、建议 |
| 社区内容审核 | 帖子内容 | 合规 / 违规 |

### 默认 Prompt

**错题分析 Prompt：**
```
你是一位小学教育专家。分析这张错题图片，判断：
1. 错误类型：粗心（看错符号/抄错数/漏题）还是知识漏洞（概念不清/公式记错）
2. 涉及的知识点
3. 改进建议（一句话，适合 1-3 年级孩子理解）
返回 JSON 格式：{ "type": "careless|knowledge", "detail": "...", "knowledgePoint": "...", "suggestion": "..." }
```

**成长评估 Prompt：**
```
基于以下孩子的成长数据，生成阶段性评估报告：
- 错题总数：{mistakeCount}
- 任务完成率：{completionRate}%
- 物品丢失次数：{itemLossCount}
- 当前习惯：{habitTitle}
要求指出进步方面、需要关注的方面、以及给家长的具体建议。
返回 JSON 格式：{ "progress": "...", "concerns": "...", "suggestions": "..." }
```
