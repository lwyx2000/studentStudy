# 全小学阶段儿童粗心矫正系统 - 数据库表结构文档

> 版本: v1.0 | 基线日期: 2026-06-05 | 数据库: MySQL 8.0+
> 命名规范：表名 `biz_业务名`，主键 `pk_业务名`，外键 `f_关联业务名`

---

## ER 关系概览

```
biz_users ──1:N── biz_assessments
biz_users ──1:N── biz_tasks
biz_users ──1:N── biz_mistake_records
biz_users ──1:N── biz_item_loss_records
biz_users ──1:N── biz_pomodoro_sessions
biz_users ──1:N── biz_covenants
biz_users ──1:N── biz_badge_unlocks
biz_users ──1:N── biz_growth_snapshots
biz_users ──1:N── biz_diagnostic_alerts
biz_users ──1:N── biz_parent_settings
biz_users ──1:N── biz_question_items
biz_users ──1:N── biz_question_bank_imports
biz_mistake_records ──1:N── biz_mistake_reviews
biz_mistake_records ──1:1── biz_draft_papers
biz_covenants ──1:N── biz_covenant_signatures
biz_community_posts ──1:N── biz_post_replies
biz_articles ──1:N── biz_article_bookmarks
```

---

## 1. biz_users - 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_users | VARCHAR(36) | PK | 主键(UUID) |
| name | VARCHAR(50) | NOT NULL | 用户名(孩子或家长昵称) |
| role | VARCHAR(10) | NOT NULL | 角色('child'或'parent') |
| grade | TINYINT | NULL | 物理年级(1-6,仅child) |
| avatar_url | VARCHAR(255) | NULL | 头像URL |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NULL | 关联家长(仅child) |
| sunlight_points | INT | DEFAULT 0 | 累计阳光值 |
| streak_days | INT | DEFAULT 0 | 连续打卡天数 |
| is_onboarded | TINYINT(1) | DEFAULT 0 | 是否完成注册评估 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

索引: `idx_users_f_users`(f_users), `idx_users_role_grade`(role, grade)

---

## 2. biz_assessments - 执行功能评估表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_assessments | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| focus_attention | TINYINT | NOT NULL | 专注持久度评分(1-5) |
| organization | TINYINT | NOT NULL | 物品整洁度评分(1-5) |
| emotional_control | TINYINT | NOT NULL | 情绪克制力评分(1-5) |
| planning | TINYINT | NOT NULL | 计划启动力评分(1-5) |
| impulse_control | TINYINT | NOT NULL | 冲动抑制力评分(1-5) |
| recommended_level | TINYINT | NOT NULL | 推荐难度等级(1-5) |
| task_density | VARCHAR(20) | NOT NULL | 任务密度(low/medium/high) |
| source | VARCHAR(20) | DEFAULT 'initial' | 来源(initial/dynamic修正) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 评估时间 |

索引: `idx_assessments_f_users`(f_users)

---

## 3. biz_tasks - 每日任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_tasks | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 任务标题 |
| description | TEXT | NULL | 任务描述 |
| type | VARCHAR(20) | NOT NULL | 任务类型(habit/game/organization/mistake_review/focus_exercise) |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态(pending/completed/skipped) |
| reward_points | TINYINT | DEFAULT 10 | 奖励阳光值 |
| icon | VARCHAR(50) | NULL | 任务图标标识 |
| week_day | VARCHAR(10) | NULL | 对应星期 |
| assigned_date | DATE | NOT NULL | 分配日期 |
| completed_at | DATETIME | NULL | 完成时间 |
| completion_photo_url | VARCHAR(255) | NULL | 完成拍照URL |
| f_habit_sops | VARCHAR(36) | FK -> biz_habit_sops.pk_habit_sops, NULL | 关联SOP |

索引: `idx_tasks_user_date`(f_users, assigned_date), `idx_tasks_status`(status)

---

## 4. biz_habit_sops - 习惯标准操作程序表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_habit_sops | VARCHAR(36) | PK | 主键(UUID) |
| title | VARCHAR(100) | NOT NULL | SOP标题 |
| week_number | TINYINT | NOT NULL | 周数 |
| grade_range | VARCHAR(10) | NOT NULL | 适用年级范围(如"1-2","3-4","5-6") |
| difficulty_level | TINYINT | NOT NULL | 适配难度等级 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 5. biz_sop_steps - SOP步骤表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_sop_steps | VARCHAR(36) | PK | 主键(UUID) |
| f_habit_sops | VARCHAR(36) | FK -> biz_habit_sops.pk_habit_sops, NOT NULL | 关联SOP |
| `order` | TINYINT | NOT NULL | 步骤顺序 |
| instruction | TEXT | NOT NULL | 步骤说明 |
| image_url | VARCHAR(255) | NULL | 示例图URL |
| gif_url | VARCHAR(255) | NULL | 示例GIF/视频URL |

---

## 6. biz_mistake_records - 错题记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_mistake_records | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| subject | VARCHAR(30) | NOT NULL | 科目(math/chinese/english/science) |
| image_url | VARCHAR(255) | NOT NULL | 错题图片URL |
| recognized_text | TEXT | NULL | OCR识别文本 |
| is_carelessness | TINYINT(1) | NOT NULL | 是否粗心 |
| category | VARCHAR(30) | NULL | 粗心分类(12类) |
| knowledge_point | VARCHAR(100) | NULL | 知识点标记 |
| grade | TINYINT | NOT NULL | 当前年级 |
| curriculum_chapter | VARCHAR(100) | NULL | 教材章节 |
| review_strategy | VARCHAR(30) | DEFAULT '3day-repeat' | 复习策略 |
| next_review_at | DATETIME | NOT NULL | 下次复习时间 |
| review_count | TINYINT | DEFAULT 0 | 已复习次数 |
| resolved | TINYINT(1) | DEFAULT 0 | 是否已解决 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

索引: `idx_mistake_user_subject`(f_users, subject), `idx_mistake_category`(category), `idx_mistake_next_review`(next_review_at)

**12类粗心分类 (category)**:
- `symbol_error` 看错符号 / `unit_missing` 漏写单位 / `misread_details` 读题遗漏
- `copying_error` 抄写错误 / `skipped_step` 跳步计算 / `rushing` 急于求成
- `lost_focus` 注意力涣散 / `messy_writing` 书写混乱 / `format_error` 格式错误
- `spelling_slip` 笔误/拼写 / `wild_guess` 盲目猜测 / `something_else` 其他

---

## 7. biz_mistake_reviews - 错题复习记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_mistake_reviews | VARCHAR(36) | PK | 主键(UUID) |
| f_mistake_records | VARCHAR(36) | FK -> biz_mistake_records.pk_mistake_records, NOT NULL | 关联错题 |
| can_resolve_now | TINYINT(1) | NOT NULL | 本次能否独立做对 |
| confidence_level | TINYINT | NULL | 信心等级(1-5) |
| reviewed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 复习时间 |
| next_review_at | DATETIME | NULL | 间隔重复下次复习时间 |

---

## 8. biz_draft_papers - 草稿纸表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_draft_papers | VARCHAR(36) | PK | 主键(UUID) |
| f_mistake_records | VARCHAR(36) | FK -> biz_mistake_records.pk_mistake_records, NOT NULL | 关联错题 |
| image_url | VARCHAR(255) | NOT NULL | 草稿纸图片URL |
| chaos_zones | JSON | NULL | 检测到的混乱区域 |
| uploaded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 上传时间 |

---

## 9. biz_item_loss_records - 物品丢失记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_item_loss_records | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| item_name | VARCHAR(50) | NOT NULL | 物品名称 |
| lost_location | VARCHAR(30) | NOT NULL | 丢失地点(school/bus/home/playground/other) |
| estimated_cost | DECIMAL(10,2) | DEFAULT 0 | 估计金额损失 |
| lost_date | DATE | NOT NULL | 丢失日期 |
| frequency_30d | TINYINT | DEFAULT 1 | 30天内丢失频次 |
| is_high_frequency | TINYINT(1) | DEFAULT 0 | 是否高频(30天>=3次) |
| suggestion | TEXT | NULL | 系统生成的急救建议 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 记录时间 |

索引: `idx_loss_user_item`(f_users, item_name), `idx_loss_frequency`(frequency_30d)

---

## 10. biz_before_after_photos - 收纳前后对比表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_before_after_photos | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| before_image_url | VARCHAR(255) | NOT NULL | 收纳前照片 |
| after_image_url | VARCHAR(255) | NOT NULL | 收纳后照片 |
| organization_score | TINYINT | NULL | AI评分(1-10) |
| points_earned | TINYINT | DEFAULT 15 | 获得阳光值 |
| uploaded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 上传时间 |

---

## 11. biz_pomodoro_sessions - 番茄钟会话表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_pomodoro_sessions | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| subject | VARCHAR(30) | NOT NULL | 科目 |
| task_description | TEXT | NULL | 任务描述 |
| estimated_minutes | TINYINT | NOT NULL | 预估用时 |
| actual_minutes | TINYINT | NULL | 实际用时 |
| time_drain_reason | VARCHAR(30) | NULL | 耗时原因 |
| start_time | DATETIME | NOT NULL | 开始时间 |
| end_time | DATETIME | NULL | 结束时间 |
| uncertain_count | TINYINT | DEFAULT 0 | 不确定题目标记数 |
| status | VARCHAR(20) | DEFAULT 'running' | 状态(running/completed/abandoned) |

索引: `idx_pomodoro_user_date`(f_users, start_time)

---

## 12. biz_pomodoro_uncertain_marks - 不确定题目标记表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_pomodoro_uncertain_marks | VARCHAR(36) | PK | 主键(UUID) |
| f_pomodoro_sessions | VARCHAR(36) | FK -> biz_pomodoro_sessions.pk_pomodoro_sessions, NOT NULL | 关联会话 |
| question_number | TINYINT | NULL | 题号 |
| subject | VARCHAR(30) | NULL | 科目 |
| auto_linked_mistake | TINYINT(1) | DEFAULT 0 | 是否自动关联到错题本 |
| marked_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 标记时间 |

---

## 13. biz_growth_snapshots - 成长数据快照表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_growth_snapshots | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| snapshot_date | DATE | NOT NULL | 快照日期 |
| mistake_rate | DECIMAL(5,4) | NULL | 漏题率 |
| item_loss_rate | TINYINT | NULL | 丢东西频次(月) |
| task_completion_rate | DECIMAL(5,4) | NULL | 任务完成率 |
| focus_score | TINYINT | NULL | 专注评分 |
| neatness_score | TINYINT | NULL | 整洁评分 |
| metacognition_score | TINYINT | NULL | 元认知评分 |
| emotion_score | TINYINT | NULL | 情绪评分 |
| source | VARCHAR(20) | DEFAULT 'daily' | 来源(daily/weekly/monthly) |

索引: `idx_growth_user_date`(f_users, snapshot_date), UNIQUE(f_users, snapshot_date, source)

---

## 14. biz_diagnostic_alerts - 诊断预警表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_diagnostic_alerts | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 标题 |
| description | TEXT | NOT NULL | 描述 |
| suggestion | TEXT | NOT NULL | 建议措施 |
| severity | VARCHAR(20) | NOT NULL | 严重程度(info/warning/positive) |
| related_metric | VARCHAR(50) | NULL | 关联指标 |
| metric_change | DECIMAL(5,2) | NULL | 指标变化百分比 |
| is_read | TINYINT(1) | DEFAULT 0 | 是否已读 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

索引: `idx_alerts_user_severity`(f_users, severity)

---

## 15. biz_badges - 勋章定义表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_badges | VARCHAR(36) | PK | 主键(UUID) |
| name | VARCHAR(50) | NOT NULL | 勋章名称 |
| description | TEXT | NOT NULL | 描述 |
| icon | VARCHAR(50) | NOT NULL | 图标标识 |
| color | VARCHAR(20) | NOT NULL | 颜色 |
| requirement | TEXT | NOT NULL | 解锁条件描述 |
| requirement_type | VARCHAR(30) | NOT NULL | 条件类型 |
| requirement_value | INT | NOT NULL | 条件数值 |
| reward_points | TINYINT | DEFAULT 50 | 解锁奖励阳光值 |

---

## 16. biz_badge_unlocks - 勋章解锁记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_badge_unlocks | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| f_badges | VARCHAR(36) | FK -> biz_badges.pk_badges, NOT NULL | 关联勋章 |
| unlocked_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 解锁时间 |

UNIQUE(f_users, f_badges)

---

## 17. biz_covenants - 成长契约表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_covenants | VARCHAR(36) | PK | 主键(UUID) |
| f_users_child | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联孩子 |
| f_users_parent | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联家长 |
| goal | TEXT | NOT NULL | 契约目标 |
| reward | VARCHAR(100) | NOT NULL | 奖励描述 |
| reward_type | VARCHAR(20) | NOT NULL | 奖励类型(experience/material/custom) |
| nudge_message | TEXT | NULL | 系统提示(防贿赂) |
| status | VARCHAR(20) | DEFAULT 'draft' | 状态(draft/active/completed/expired) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| completed_at | DATETIME | NULL | 完成时间 |

---

## 18. biz_covenant_signatures - 契约签署表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_covenant_signatures | VARCHAR(36) | PK | 主键(UUID) |
| f_covenants | VARCHAR(36) | FK -> biz_covenants.pk_covenants, NOT NULL | 关联契约 |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 签署人 |
| signer_role | VARCHAR(10) | NOT NULL | 角色(child/parent) |
| signature_data | TEXT | NULL | 手写签名数据(base64) |
| signed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 签署时间 |

UNIQUE(f_covenants, signer_role)

---

## 19. biz_parent_settings - 家长设置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_parent_settings | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL, UNIQUE | 关联家长 |
| difficulty_level | TINYINT | DEFAULT 2 | 难度等级(1-3) |
| daily_reminder | TINYINT(1) | DEFAULT 1 | 每日提醒 |
| achievement_notification | TINYINT(1) | DEFAULT 1 | 成就通知 |
| weekly_report | TINYINT(1) | DEFAULT 1 | 周报 |
| school_sync | TINYINT(1) | DEFAULT 0 | 学校数据共享 |
| school_sync_code | VARCHAR(20) | NULL | 学校共享邀请码 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

---

## 20. biz_community_posts - 社区帖子表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_community_posts | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 作者(匿名化展示) |
| title | VARCHAR(200) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| tags | JSON | NULL | 标签数组 |
| reply_count | TINYINT | DEFAULT 0 | 回复数 |
| like_count | TINYINT | DEFAULT 0 | 点赞数 |
| has_expert_answer | TINYINT(1) | DEFAULT 0 | 是否有专家回答 |
| is_anonymous | TINYINT(1) | DEFAULT 1 | 是否匿名 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 21. biz_post_replies - 帖子回复表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_post_replies | VARCHAR(36) | PK | 主键(UUID) |
| f_community_posts | VARCHAR(36) | FK -> biz_community_posts.pk_community_posts, NOT NULL | 关联帖子 |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 作者 |
| content | TEXT | NOT NULL | 回复内容 |
| is_expert | TINYINT(1) | DEFAULT 0 | 是否专家回复 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 22. biz_articles - 循证资源表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_articles | VARCHAR(36) | PK | 主键(UUID) |
| title | VARCHAR(200) | NOT NULL | 标题 |
| summary | TEXT | NULL | 摘要 |
| content_url | VARCHAR(255) | NOT NULL | 内容URL |
| category | VARCHAR(30) | NOT NULL | 分类 |
| type | VARCHAR(20) | NOT NULL | 类型(article/video/cbt) |
| reading_time_minutes | TINYINT | NULL | 阅读时长 |
| image_url | VARCHAR(255) | NULL | 封面图 |
| author | VARCHAR(100) | NULL | 作者/专家 |
| published_at | DATETIME | NOT NULL | 发布时间 |

索引: `idx_articles_category`(category)

---

## 23. biz_article_bookmarks - 文章收藏表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_article_bookmarks | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| f_articles | VARCHAR(36) | FK -> biz_articles.pk_articles, NOT NULL | 关联文章 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 收藏时间 |

UNIQUE(f_users, f_articles)

---

## 24. biz_shared_covenants - 共享契约表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_shared_covenants | VARCHAR(36) | PK | 主键(UUID) |
| f_covenants | VARCHAR(36) | FK -> biz_covenants.pk_covenants, NOT NULL | 关联原始契约 |
| like_count | TINYINT | DEFAULT 0 | 点赞数 |
| shared_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 分享时间 |

---

## 25. biz_growth_reports - 生成报告表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_growth_reports | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| period | VARCHAR(20) | NOT NULL | 时间范围(semester/year/all) |
| pdf_url | VARCHAR(255) | NOT NULL | PDF URL |
| include_peer_comparison | TINYINT(1) | DEFAULT 1 | 是否含同龄对比 |
| generated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 生成时间 |

---

## 26. biz_task_weekly_progress - 每周打卡进度表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_task_weekly_progress | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| week_number | TINYINT | NOT NULL | 周数 |
| year | SMALLINT | NOT NULL | 年份 |
| completed_days | TINYINT | DEFAULT 0 | 完成天数 |
| total_days | TINYINT | DEFAULT 7 | 总天数 |
| progress_percent | DECIMAL(5,2) | DEFAULT 0 | 完成百分比 |
| f_habit_sops | VARCHAR(36) | FK -> biz_habit_sops.pk_habit_sops | 关联本周习惯 |

UNIQUE(f_users, year, week_number)

---

## 27. biz_question_items - 藏宝库题目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_question_items | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| subject | VARCHAR(20) | NOT NULL | 科目(math/chinese/english/science/other) |
| type | VARCHAR(20) | NOT NULL | 题型(choice/fill/calculation/composition/other) |
| content | TEXT | NOT NULL | 题目正文 |
| answer | TEXT | NULL | 参考答案 |
| image_url | VARCHAR(255) | NULL | 题目图片URL |
| grade | TINYINT | NOT NULL | 适用年级(1-6) |
| chapter | VARCHAR(100) | NULL | 教材章节 |
| knowledge_points | JSON | NULL | 知识点标签数组 |
| difficulty | TINYINT | NOT NULL | 难度(1-5) |
| tags | JSON | NULL | 自定义标签数组 |
| is_carelessness | TINYINT(1) | DEFAULT 0 | 是否粗心型错误 |
| mistake_category | VARCHAR(30) | NULL | 粗心分类 |
| review_count | TINYINT | DEFAULT 0 | 已复习次数 |
| resolved | TINYINT(1) | DEFAULT 0 | 是否已解决 |
| source | VARCHAR(20) | DEFAULT 'manual' | 来源(manual/photo/import) |
| f_question_bank_imports | VARCHAR(36) | FK -> biz_question_bank_imports.pk_question_bank_imports, NULL | 关联导入批次 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

索引: `idx_question_user_subject`(f_users, subject), `idx_question_resolved`(resolved), `idx_question_source`(source), `idx_question_import`(f_question_bank_imports)

---

## 28. biz_question_bank_imports - 题库导入批次表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_question_bank_imports | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| file_name | VARCHAR(255) | NOT NULL | 导入文件名 |
| total_count | INT | DEFAULT 0 | 文件中题目总数 |
| imported_count | INT | DEFAULT 0 | 成功导入数 |
| failed_count | INT | DEFAULT 0 | 失败数 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态(pending/success/partial/failed) |
| errors | JSON | NULL | 错误详情数组 |
| imported_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 导入时间 |

索引: `idx_import_user`(f_users)

---

## 29. biz_question_print_jobs - 题目打印任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_question_print_jobs | VARCHAR(36) | PK | 主键(UUID) |
| f_users | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 打印标题 |
| mode | VARCHAR(20) | NOT NULL | 选题模式(manual/ai) |
| question_ids | JSON | NOT NULL | 选中题目ID数组 |
| include_answer | TINYINT(1) | DEFAULT 0 | 是否附带答案 |
| question_count | INT | NOT NULL | 题目数量 |
| printed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 打印时间 |

索引: `idx_print_user`(f_users)

---

## 30. biz_habit_assignments - 习惯布置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_habit_assignments | VARCHAR(36) | PK | 主键(UUID) |
| f_users_child | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联孩子 |
| f_users_parent | VARCHAR(36) | FK -> biz_users.pk_users, NOT NULL | 关联家长 |
| title | VARCHAR(100) | NOT NULL | 习惯名称 |
| description | TEXT | NULL | 习惯说明 |
| icon | VARCHAR(10) | DEFAULT '✅' | 图标 |
| reward_points | TINYINT | DEFAULT 10 | 奖励阳光值 |
| week_number | TINYINT | DEFAULT 1 | 周数(1-52) |
| active | TINYINT(1) | DEFAULT 1 | 是否活跃 |
| assigned_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 布置时间 |

索引: `idx_habit_child`(f_users_child), `idx_habit_parent`(f_users_parent), `idx_habit_active`(active)

---

## 31. biz_habit_sop_steps - 习惯布置步骤表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_habit_sop_steps | VARCHAR(36) | PK | 主键(UUID) |
| f_habit_assignments | VARCHAR(36) | FK -> biz_habit_assignments.pk_habit_assignments, NOT NULL | 关联习惯布置 |
| step_order | TINYINT | NOT NULL | 步骤顺序 |
| instruction | TEXT | NOT NULL | 步骤说明 |
| image_url | VARCHAR(255) | NULL | 步骤配图URL |
| gif_url | VARCHAR(255) | NULL | 步骤GIF URL |

索引: `idx_sop_habit`(f_habit_assignments), UNIQUE(f_habit_assignments, step_order)

---

## 命名规范总结

| 规范 | 格式 | 示例 |
|------|------|------|
| 表名 | `biz_业务名` | `biz_users`, `biz_mistake_records` |
| 主键 | `pk_业务名` | `pk_users`, `pk_mistake_records` |
| 外键 | `f_关联业务名` | `f_users`, `f_mistake_records` |
| 唯一外键(需区分) | `f_业务名_角色` | `f_users_child`, `f_users_parent` |
