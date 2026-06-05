# 全小学阶段儿童粗心矫正系统 - 后端接口文档

> 版本: v1.0 | 基线日期: 2026-06-05

---

## 1. 通用约定

### 1.1 请求格式

- 基础路径: `/api/v1`
- Content-Type: `application/json` (文件上传除外)
- 文件上传: `multipart/form-data`
- 认证: Bearer Token (JWT)

### 1.2 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 参数校验失败 |
| 1002 | 未认证 |
| 1003 | 无权限 |
| 2001 | 资源不存在 |
| 3001 | 业务逻辑错误 |

### 1.3 分页参数

- `page`: 页码，默认1
- `pageSize`: 每页数量，默认20
- 响应包含 `total`, `page`, `pageSize`, `list`

---

## 2. 认证模块

### 2.1 注册

```
POST /api/v1/auth/register
```

请求:
```json
{
  "name": "Leo",
  "grade": 3,
  "role": "child",
  "parentId": "optional_parent_id"
}
```

响应:
```json
{
  "data": {
    "id": "user_xxx",
    "name": "Leo",
    "grade": 3,
    "role": "child",
    "token": "jwt_token"
  }
}
```

### 2.2 登录

```
POST /api/v1/auth/login
```

请求:
```json
{
  "name": "Leo",
  "role": "child"
}
```

响应:
```json
{
  "data": {
    "token": "jwt_token",
    "user": { "id", "name", "grade", "role", "avatarUrl" }
  }
}
```

### 2.3 获取当前用户信息

```
GET /api/v1/auth/me
```

响应: 当前用户完整 profile

---

## 3. 执行功能评估模块

### 3.1 提交评估

```
POST /api/v1/assessments
```

请求:
```json
{
  "userId": "user_xxx",
  "focusAttention": 3,
  "organization": 2,
  "emotionalControl": 4
}
```

响应:
```json
{
  "data": {
    "id": "assessment_xxx",
    "recommendedLevel": 3,
    "taskDensity": "medium",
    "createdAt": "2026-06-05T10:00:00Z"
  }
}
```

### 3.2 获取评估结果

```
GET /api/v1/assessments/:userId
```

响应: 评估结果 + 推荐等级

### 3.3 更新评估(动态修正)

```
PUT /api/v1/assessments/:assessmentId
```

请求: 同提交评估，系统根据最新打卡数据自动修正推荐等级

---

## 4. 每日任务模块

### 4.1 获取今日任务列表

```
GET /api/v1/tasks/today/:userId
```

响应:
```json
{
  "data": [
    {
      "id": "task_xxx",
      "title": "指读圈号",
      "description": "动笔前用手指着读题并圈出大题号",
      "type": "habit",
      "status": "pending",
      "rewardPoints": 10,
      "weekDay": "Monday"
    }
  ]
}
```

### 4.2 完成任务

```
POST /api/v1/tasks/:taskId/complete
```

请求:
```json
{
  "completedAt": "2026-06-05T10:30:00Z",
  "photoUrl": "optional_photo_url"
}
```

响应:
```json
{
  "data": {
    "points": 10,
    "totalSunlightPoints": 130,
    "streakDays": 5
  }
}
```

### 4.3 获取习惯SOP

```
GET /api/v1/tasks/habit-sop/:userId
```

响应:
```json
{
  "data": {
    "id": "sop_xxx",
    "title": "指读圈号标准操作",
    "weekNumber": 2,
    "steps": [
      { "order": 1, "instruction": "手指指着题目逐行阅读", "imageUrl": "...", "gifUrl": "..." },
      { "order": 2, "instruction": "用铅笔圈出每道大题的题号", "imageUrl": "...", "gifUrl": "..." },
      { "order": 3, "instruction": "完成后回头看一圈确认没有遗漏", "imageUrl": "...", "gifUrl": "..." }
    ]
  }
}
```

### 4.4 获取本周习惯进度

```
GET /api/v1/tasks/weekly-progress/:userId
```

响应:
```json
{
  "data": {
    "weekNumber": 2,
    "progressPercent": 33,
    "completedDays": 1,
    "totalDays": 3,
    "streakDays": 5
  }
}
```

---

## 5. 智能错题本模块

### 5.1 上传错题图片

```
POST /api/v1/mistakes/upload
```

请求: multipart/form-data, 字段 `image` (文件)

响应:
```json
{
  "data": {
    "imageUrl": "/uploads/mistake_xxx.jpg",
    "recognizedText": "自动OCR识别的题目文本(可选)"
  }
}
```

### 5.2 创建错题记录

```
POST /api/v1/mistakes
```

请求:
```json
{
  "subject": "math",
  "imageUrl": "/uploads/mistake_xxx.jpg",
  "isCarelessness": true,
  "category": "symbol_error",
  "knowledgePoint": "optional_knowledge_point_tag",
  "grade": 3,
  "curriculumChapter": "第3单元"
}
```

响应:
```json
{
  "data": {
    "id": "mistake_xxx",
    "reviewScheduledAt": "2026-06-12T10:00:00Z",
    "reviewStrategy": "3day-repeat",
    "subject": "math",
    "category": "symbol_error",
    "createdAt": "2026-06-05T10:00:00Z"
  }
}
```

### 5.3 获取错题列表

```
GET /api/v1/mistakes/:userId?page=1&pageSize=20&subject=math&category=symbol_error
```

响应: 分页错题列表

### 5.4 获取今日待复习错题数

```
GET /api/v1/mistakes/today-review/:userId
```

响应:
```json
{
  "data": {
    "count": 5,
    "mistakes": [ { "id", "subject", "imageUrl", "reviewStrategy" } ]
  }
}
```

### 5.5 完成错题复习

```
POST /api/v1/mistakes/:mistakeId/review
```

请求:
```json
{
  "canResolveNow": true,
  "confidenceLevel": 4
}
```

响应: 更新复习策略(间隔重复算法)

### 5.6 上传草稿纸

```
POST /api/v1/mistakes/:mistakeId/draft-paper
```

请求: multipart/form-data, 字段 `image`

响应:
```json
{
  "data": {
    "draftImageUrl": "/uploads/draft_xxx.jpg",
    "chaosZones": [
      { "x": 120, "y": 80, "width": 60, "height": 40, "severity": "high" }
    ]
  }
}
```

---

## 6. 物品流失追踪模块

### 6.1 报告物品丢失

```
POST /api/v1/items/loss
```

请求:
```json
{
  "itemName": "橡皮",
  "lostLocation": "school",
  "estimatedCost": 5,
  "lostDate": "2026-06-05"
}
```

响应:
```json
{
  "data": {
    "id": "loss_xxx",
    "frequency": 3,
    "isHighFrequency": true,
    "suggestion": "建议立刻在橡皮上贴上醒目的荧光色姓名贴"
  }
}
```

### 6.2 获取物品丢失列表

```
GET /api/v1/items/loss/:userId?page=1&pageSize=20
```

响应: 分页丢失记录

### 6.3 获取物品丢失统计

```
GET /api/v1/items/stats/:userId?period=30days
```

响应:
```json
{
  "data": {
    "radarData": { "school": 5, "bus": 2, "home": 3, "playground": 1, "other": 0 },
    "totalCost": 45,
    "highFrequencyItems": [
      { "itemName": "橡皮", "frequency": 3, "suggestion": "...", "estimatedCost": 15 }
    ],
    "totalLossRecords": 11
  }
}
```

### 6.4 上传收纳前后对比

```
POST /api/v1/items/before-after
```

请求: multipart/form-data, 字段 `beforeImage`, `afterImage`

响应:
```json
{
  "data": {
    "points": 15,
    "organizationScore": 7
  }
}
```

---

## 7. 成长档案与预警模块

### 7.1 获取成长趋势数据

```
GET /api/v1/growth/trend/:userId?period=semester
```

响应:
```json
{
  "data": {
    "trendData": [
      { "date": "2026-03", "mistakeRate": 0.25, "itemLossRate": 3, "taskCompletionRate": 0.78 },
      { "date": "2026-04", "mistakeRate": 0.20, "itemLossRate": 2, "taskCompletionRate": 0.82 },
      { "date": "2026-05", "mistakeRate": 0.17, "itemLossRate": 1, "taskCompletionRate": 0.85 }
    ],
    "period": "semester"
  }
}
```

### 7.2 获取同龄常模对比

```
GET /api/v1/growth/peer-comparison/:userId
```

响应:
```json
{
  "data": {
    "childData": { "focus": 65, "neatness": 45, "metacognition": 35, "emotion": 70 },
    "peerAverage": { "focus": 50, "neatness": 55, "metacognition": 40, "emotion": 60 },
    "gradeNorm": 3
  }
}
```

### 7.3 获取智能诊断预警

```
GET /api/v1/growth/alerts/:userId
```

响应:
```json
{
  "data": [
    {
      "id": "alert_xxx",
      "title": "阶段性发展发现",
      "description": "近7天看错符号错误环比上升25%",
      "suggestion": "将晚上写作业的中间休息频率提高至写20分钟休息5分钟",
      "severity": "warning",
      "relatedMetric": "symbol_error_rate",
      "createdAt": "2026-06-05T08:00:00Z"
    }
  ]
}
```

### 7.4 生成PDF成长报告

```
POST /api/v1/growth/report/:userId
```

请求:
```json
{
  "period": "semester",
  "includePeerComparison": true,
  "format": "pdf"
}
```

响应:
```json
{
  "data": {
    "pdfUrl": "/reports/growth_report_xxx.pdf",
    "generatedAt": "2026-06-05T10:00:00Z"
  }
}
```

---

## 8. 番茄钟/时间管理模块

### 8.1 启动番茄钟

```
POST /api/v1/pomodoro/start
```

请求:
```json
{
  "estimatedMinutes": 30,
  "subject": "math",
  "taskDescription": "数学作业第3单元"
}
```

响应:
```json
{
  "data": {
    "sessionId": "pom_xxx",
    "startTime": "2026-06-05T10:00:00Z",
    "estimatedMinutes": 30
  }
}
```

### 8.2 结束番茄钟

```
POST /api/v1/pomodoro/:sessionId/finish
```

请求:
```json
{
  "actualMinutes": 45,
  "timeDrainReason": "calculation",
  "selfReflection": "验算耗时较多"
}
```

响应:
```json
{
  "data": {
    "sessionId": "pom_xxx",
    "estimatedMinutes": 30,
    "actualMinutes": 45,
    "difference": 15,
    "subject": "math",
    "timeDrainReason": "calculation"
  }
}
```

### 8.3 标记不确定题目

```
POST /api/v1/pomodoro/:sessionId/uncertain
```

请求: `{ "questionNumber": 3, "subject": "math" }`

响应: `{ "data": { "totalCount": 3 } }`

### 8.4 获取番茄钟历史

```
GET /api/v1/pomodoro/history/:userId?period=week
```

响应: 番茄钟会话列表，包含预估vs实际对照数据

---

## 9. 成长契约与勋章模块

### 9.1 创建成长契约

```
POST /api/v1/covenants
```

请求:
```json
{
  "goal": "连续7天完成每日习惯打卡",
  "reward": "family_movie",
  "rewardType": "experience",
  "customReward": "optional_custom_reward_description"
}
```

响应:
```json
{
  "data": {
    "id": "covenant_xxx",
    "goal": "连续7天完成每日习惯打卡",
    "reward": "周五亲子电影夜",
    "rewardType": "experience",
    "nudgeMessage": "体验类奖励比物质奖励更有助于内在驱动",
    "status": "active",
    "createdAt": "2026-06-05T10:00:00Z"
  }
}
```

### 9.2 获取契约列表

```
GET /api/v1/covenants/:userId
```

响应: 契约列表

### 9.3 签署契约

```
POST /api/v1/covenants/:covenantId/sign
```

请求: `{ "signerRole": "child|parent" }`

### 9.4 完成契约

```
POST /api/v1/covenants/:covenantId/complete
```

### 9.5 获取勋章列表

```
GET /api/v1/badges/:userId
```

响应:
```json
{
  "data": [
    {
      "id": "badge_xxx",
      "name": "3日坚持勋章",
      "description": "连续3天完成打卡",
      "icon": "fire",
      "color": "red",
      "unlocked": true,
      "unlockedAt": "2026-06-03",
      "requirement": "连续3天完成每日习惯打卡"
    }
  ]
}
```

### 9.6 解锁勋章

```
POST /api/v1/badges/:badgeId/unlock
```

响应: `{ "data": { "unlocked": true, "pointsEarned": 50 } }`

---

## 10. 打印与物理核销模块

### 10.1 生成纸质打卡单PDF

```
POST /api/v1/print/checklist/:userId
```

请求:
```json
{
  "weekNumber": 2,
  "includeMistakeArea": true,
  "format": "a4"
}
```

响应:
```json
{
  "data": {
    "pdfUrl": "/printables/checklist_week2_xxx.pdf"
  }
}
```

### 10.2 扫描上传完成打卡单

```
POST /api/v1/print/scan
```

请求: multipart/form-data, 字段 `image` (拍照的纸质打卡单)

响应:
```json
{
  "data": {
    "recognized": true,
    "recognizedChecks": { "mon_habit": true, "tue_habit": true, "wed_habit": false },
    "completionRate": 0.67,
    "pointsEarned": 15,
    "reportUrl": "/reports/scan_report_xxx.pdf"
  }
}
```

---

## 11. 家长控制模块

### 11.1 获取家长设置

```
GET /api/v1/parent/settings/:userId
```

响应:
```json
{
  "data": {
    "difficultyLevel": 2,
    "dailyReminder": true,
    "achievementNotification": true,
    "weeklyReport": true,
    "schoolSync": false,
    "schoolSyncCode": "optional_invite_code"
  }
}
```

### 11.2 更新家长设置

```
PUT /api/v1/parent/settings/:userId
```

请求: Partial `ParentSettings`

响应: 更新后的完整设置

---

## 12. 社区花园模块

### 12.1 获取社区帖子

```
GET /api/v1/community/posts?page=1&pageSize=20&tag=CBT
```

响应: 分页帖子列表

### 12.2 创建帖子

```
POST /api/v1/community/posts
```

请求:
```json
{
  "title": "孩子总是丢橡皮怎么办?",
  "content": "...",
  "tags": ["物品追踪", "CBT"]
}
```

响应: 创建的帖子(匿名化)

### 12.3 获取共享契约

```
GET /api/v1/community/covenants?page=1&pageSize=10
```

响应: 其他家庭分享的契约(匿名化)

### 12.4 点赞契约

```
POST /api/v1/community/covenants/:covenantId/like
```

---

## 13. 循证资源模块

### 13.1 获取文章列表

```
GET /api/v1/articles?category=executive_function&page=1&pageSize=20
```

响应: 分页文章资源列表

### 13.2 获取推荐文章

```
GET /api/v1/articles/suggested/:userId
```

响应: 根据孩子评估结果推荐的个性化文章列表

### 13.3 收藏/取消收藏文章

```
POST /api/v1/articles/:articleId/bookmark
DELETE /api/v1/articles/:articleId/bookmark
```