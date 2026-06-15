# 全小学阶段儿童粗心矫正系统 - 后端接口文档

> 版本: v1.0 | 基线日期: 2026-06-05 | 数据库: MySQL 8.0+
> 数据库命名规范：表名 `biz_业务名`，主键 `pk_业务名`，外键 `f_关联业务名`
> 例：表 `biz_users` 主键 `pk_users`，表 `biz_assessments` 外键 `f_users` → `biz_users.pk_users`

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
  "emotionalControl": 4,
  "planning": 3,
  "impulseControl": 4
}
```

响应:
```json
{
  "data": {
    "id": "assessment_xxx",
    "recommendedLevel": 3,
    "taskDensity": "medium",
    "assessmentDimensions": 5,
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
    "checkedCount": 5,
    "report": "已识别 5 个勾选，建议继续保持指读圈号。",
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

---

## 14. 藏宝库（题库）模块

### 14.1 获取题目列表

```
GET /api/v1/questions/:userId?page=1&pageSize=20&subject=math&resolved=false&source=manual&sort=createdAt&order=desc
```

查询参数:
- `subject`: 科目过滤(math/chinese/english/science/other)
- `resolved`: 是否已解决(true/false)
- `source`: 来源过滤(manual/photo/import)
- `sort`: 排序字段(createdAt/updatedAt/difficulty/reviewCount)
- `order`: 排序方向(asc/desc)

响应:
```json
{
  "data": {
    "total": 45,
    "page": 1,
    "pageSize": 20,
    "list": [
      {
        "id": "q_xxx",
        "subject": "math",
        "type": "calculation",
        "content": "计算：3.25 × 4 + 0.5 =",
        "answer": "13.5",
        "grade": 3,
        "chapter": "第3单元 小数乘法",
        "knowledgePoints": ["小数乘法", "混合运算"],
        "difficulty": 2,
        "tags": ["易错"],
        "isCarelessness": true,
        "mistakeCategory": "symbol_error",
        "reviewCount": 1,
        "resolved": false,
        "source": "manual",
        "createdAt": "2026-06-01T10:00:00Z",
        "updatedAt": "2026-06-01T10:00:00Z"
      }
    ]
  }
}
```

### 14.2 手工创建题目

```
POST /api/v1/questions
```

请求:
```json
{
  "subject": "math",
  "type": "calculation",
  "content": "计算：3.25 × 4 + 0.5 =",
  "answer": "13.5",
  "grade": 3,
  "chapter": "第3单元",
  "knowledgePoints": ["小数乘法", "混合运算"],
  "difficulty": 2,
  "tags": ["易错"],
  "isCarelessness": true,
  "mistakeCategory": "symbol_error"
}
```

响应:
```json
{
  "data": {
    "id": "q_xxx",
    "createdAt": "2026-06-05T10:00:00Z"
  }
}
```

### 14.3 更新题目

```
PUT /api/v1/questions/:questionId
```

请求: 同创建题目（Partial，仅传需要更新的字段）

响应: 更新后的完整题目数据

### 14.4 删除题目

```
DELETE /api/v1/questions/:questionId
```

响应: `{ "data": { "deleted": true } }`

### 14.5 标记题目已解决

```
POST /api/v1/questions/:questionId/resolve
```

响应: `{ "data": { "resolved": true } }`

### 14.6 增加复习次数

```
POST /api/v1/questions/:questionId/review
```

响应: `{ "data": { "reviewCount": 3 } }`

### 14.7 获取题库统计概览

```
GET /api/v1/questions/stats/:userId
```

响应:
```json
{
  "data": {
    "totalCount": 45,
    "unresolvedCount": 30,
    "todayAddedCount": 3,
    "bySubject": { "math": 20, "chinese": 15, "english": 8, "science": 2 },
    "byCategory": { "symbol_error": 8, "misread_details": 5, "rushing": 3 },
    "byDifficulty": { "1": 5, "2": 12, "3": 15, "4": 8, "5": 5 }
  }
}
```

### 14.8 AI智能选题

```
POST /api/v1/questions/ai-recommend/:userId
```

请求:
```json
{
  "maxCount": 10,
  "subject": "math",
  "difficultyMin": 2
}
```

响应:
```json
{
  "data": {
    "recommendedIds": ["q_xxx", "q_yyy", "..."],
    "reason": "优先选择复习次数少、难度高、且未解决的题目"
  }
}
```

### 14.9 生成打印页面

```
POST /api/v1/questions/print
```

请求:
```json
{
  "questionIds": ["q_xxx", "q_yyy"],
  "mode": "manual",
  "title": "错题打印",
  "includeAnswer": true
}
```

响应:
```json
{
  "data": {
    "pdfUrl": "/prints/questions_print_xxx.pdf",
    "questionCount": 2,
    "generatedAt": "2026-06-05T10:00:00Z"
  }
}
```

### 14.10 导入外部题库

```
POST /api/v1/questions/import
```

请求: multipart/form-data, 字段 `file` (JSON文件)

响应:
```json
{
  "data": {
    "importId": "imp_xxx",
    "fileName": "math_questions.json",
    "totalCount": 50,
    "importedCount": 45,
    "failedCount": 5,
    "status": "partial",
    "errors": [
      "第3题: content(题目正文)为必填项",
      "第7题: subject 不合法"
    ]
  }
}
```

**导入JSON格式规范 v1.0:**
```json
{
  "version": "1.0",
  "exportedAt": "2026-06-05T10:00:00Z",
  "schoolInfo": { "name": "XX小学", "grade": 3 },
  "questions": [
    {
      "subject": "math",
      "type": "calculation",
      "content": "计算：3.25 × 4 =",
      "answer": "13",
      "grade": 3,
      "chapter": "第3单元",
      "knowledgePoints": ["小数乘法"],
      "difficulty": 2,
      "tags": ["易错"]
    }
  ]
}
```

**校验规则:**
- `version` 必须为 `"1.0"`
- `questions[].subject` 必填，且为 math/chinese/english/science/other 之一
- `questions[].type` 必填，且为 choice/fill/calculation/composition/other 之一
- `questions[].content` 必填，不能为空白
- `questions[].grade` 选填，缺省取 schoolInfo.grade 或 3
- `questions[].difficulty` 选填，范围1-5，缺省为3
- 其余字段均为选填

### 14.11 导出题库

```
POST /api/v1/questions/export
```

请求:
```json
{
  "questionIds": ["q_xxx", "q_yyy"],
  "format": "json"
}
```

响应: 以标准 v1.0 JSON 格式返回题库数据（Content-Type: application/json，Content-Disposition: attachment）

### 14.12 获取导入历史

```
GET /api/v1/questions/imports/:userId?page=1&pageSize=10
```

响应:
```json
{
  "data": {
    "total": 3,
    "list": [
      {
        "id": "imp_xxx",
        "fileName": "math_questions.json",
        "totalCount": 50,
        "importedCount": 50,
        "failedCount": 0,
        "status": "success",
        "importedAt": "2026-06-05T10:00:00Z"
      }
    ]
  }
}
```

### 14.13 获取薄弱环节分析数据

```
GET /api/v1/questions/weakness/:userId
```

响应:
```json
{
  "data": {
    "bySubject": [
      { "subject": "数学", "count": 20, "color": "#f87171" },
      { "subject": "语文", "count": 15, "color": "#60a5fa" }
    ],
    "byCategory": [
      { "category": "看错符号", "count": 8 },
      { "category": "读题遗漏", "count": 5 }
    ],
    "byKnowledgePoint": [
      { "point": "小数乘法", "count": 6 },
      { "point": "分数比较", "count": 4 }
    ],
    "byDifficulty": [
      { "level": 1, "label": "★", "count": 5 },
      { "level": 2, "label": "★★", "count": 12 },
      { "level": 3, "label": "★★★", "count": 15 },
      { "level": 4, "label": "★★★★", "count": 8 },
      { "level": 5, "label": "★★★★★", "count": 5 }
    ]
  }
}
```

---

## 15. 使用说明模块

### 15.1 获取使用说明内容

```
GET /api/v1/guide
```

响应:
```json
{
  "data": {
    "pages": [
      {
        "icon": "🌳",
        "title": "协同仪表盘",
        "path": "/dashboard",
        "purpose": "系统的核心入口页面，展示今日最需要关注的任务与即时反馈。",
        "usage": ["低年级大卡片单任务聚焦模式", "高年级数据面板模式", "点击任务卡片完成可获得阳光值"]
      }
    ],
    "commonOps": [
      { "icon": "☀️", "title": "阳光值", "desc": "完成任务、上传照片、解锁勋章均可获得" },
      { "icon": "🌱", "title": "成长树", "desc": "侧栏展示，随Level变化形态" },
      { "icon": "🖨️", "title": "打印", "desc": "习惯打卡单和错题均支持A4打印" }
    ]
  }
}
```

> 前端使用说明页面为纯静态页面，数据直接写在前端，此接口为可选的后端化方案。

---

## 16. 习惯布置模块

> 家长为孩子布置每周核心习惯，包含执行步骤SOP、奖励阳光值、周数等。孩子端自动同步活跃习惯。

### 16.1 获取孩子的习惯列表

```
GET /api/v1/habits/:childId?active=true
```

查询参数:
- `active`: 是否仅活跃习惯(true/false)，缺省返回全部

响应:
```json
{
  "data": {
    "list": [
      {
        "id": "ha_xxx",
        "childId": "u_child",
        "parentId": "u_parent",
        "title": "指读圈号",
        "description": "用手指指着题目逐字阅读，圈出关键词",
        "icon": "✅",
        "rewardPoints": 10,
        "weekNumber": 3,
        "steps": [
          { "order": 1, "instruction": "把作业本翻开到今天作业页" },
          { "order": 2, "instruction": "用手指指着题目逐字读" },
          { "order": 3, "instruction": "圈出关键词" }
        ],
        "assignedAt": "2026-06-05T10:00:00Z",
        "active": true
      }
    ]
  }
}
```

### 16.2 布置新习惯

```
POST /api/v1/habits
```

请求:
```json
{
  "childId": "u_child",
  "parentId": "u_parent",
  "title": "指读圈号",
  "description": "用手指指着题目逐字阅读，圈出关键词",
  "icon": "✅",
  "rewardPoints": 10,
  "weekNumber": 3,
  "steps": [
    { "order": 1, "instruction": "把作业本翻开到今天作业页" },
    { "order": 2, "instruction": "用手指指着题目逐字读" },
    { "order": 3, "instruction": "圈出关键词" }
  ]
}
```

响应:
```json
{
  "data": {
    "id": "ha_xxx",
    "assignedAt": "2026-06-05T10:00:00Z",
    "active": true
  }
}
```

### 16.3 更新习惯

```
PUT /api/v1/habits/:habitId
```

请求: 同布置新习惯（Partial，仅传需要更新的字段）

响应: 更新后的完整习惯数据

### 16.4 停用习惯

```
POST /api/v1/habits/:habitId/deactivate
```

响应:
```json
{
  "data": {
    "id": "ha_xxx",
    "active": false
  }
}
```

### 16.5 获取习惯执行情况统计

```
GET /api/v1/habits/:habitId/stats?days=7
```

查询参数:
- `days`: 统计最近N天，缺省7

响应:
```json
{
  "data": {
    "habitId": "ha_xxx",
    "title": "指读圈号",
    "totalDays": 7,
    "completedDays": 5,
    "completionRate": 71.4,
    "streakDays": 3
  }
}
```

---

## 附录：接口模块与数据库表映射

| 接口模块 | 主要操作表 | 主键 | 关键外键 |
|---------|-----------|------|---------|
| 2.认证 | biz_users | pk_users | f_users(自关联parent) |
| 3.评估 | biz_assessments | pk_assessments | f_users |
| 4.任务 | biz_tasks, biz_habit_sops, biz_sop_steps, biz_task_weekly_progress | pk_tasks / pk_habit_sops / pk_sop_steps / pk_task_weekly_progress | f_users, f_habit_sops |
| 5.错题本 | biz_mistake_records, biz_mistake_reviews, biz_draft_papers | pk_mistake_records / pk_mistake_reviews / pk_draft_papers | f_users, f_mistake_records |
| 6.物品追踪 | biz_item_loss_records, biz_before_after_photos | pk_item_loss_records / pk_before_after_photos | f_users |
| 7.成长档案 | biz_growth_snapshots, biz_diagnostic_alerts, biz_growth_reports | pk_growth_snapshots / pk_diagnostic_alerts / pk_growth_reports | f_users |
| 8.番茄钟 | biz_pomodoro_sessions, biz_pomodoro_uncertain_marks | pk_pomodoro_sessions / pk_pomodoro_uncertain_marks | f_users, f_pomodoro_sessions |
| 9.契约勋章 | biz_covenants, biz_covenant_signatures, biz_badges, biz_badge_unlocks | pk_covenants / pk_covenant_signatures / pk_badges / pk_badge_unlocks | f_users, f_badges, f_covenants |
| 10.打印核销 | biz_tasks | - | - |
| 11.家长控制 | biz_parent_settings | pk_parent_settings | f_users |
| 12.社区花园 | biz_community_posts, biz_post_replies, biz_shared_covenants | pk_community_posts / pk_post_replies / pk_shared_covenants | f_users, f_community_posts, f_covenants |
| 13.循证资源 | biz_articles, biz_article_bookmarks | pk_articles / pk_article_bookmarks | f_users, f_articles |
| 14.藏宝库 | biz_question_items, biz_question_bank_imports, biz_question_print_jobs | pk_question_items / pk_question_bank_imports / pk_question_print_jobs | f_users, f_question_bank_imports |
| 15.使用说明 | (无数据库表，前端静态) | - | - |
| 16.习惯布置 | biz_habit_assignments, biz_habit_sop_steps | pk_habit_assignments / pk_habit_sop_steps | f_users(child), f_users(parent) |
