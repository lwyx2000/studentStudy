# 全小学阶段儿童粗心矫正系统 - 数据库表结构文档

> 版本: v1.0 | 基线日期: 2026-06-05 | 数据库: PostgreSQL 15+

---

## ER 关系概览

```
users ──1:N── assessments
users ──1:N── tasks
users ──1:N── mistake_records
users ──1:N── item_loss_records
users ──1:N── pomodoro_sessions
users ──1:N── covenants
users ──1:N── badge_unlocks
users ──1:N── growth_snapshots
users ──1:N── diagnostic_alerts
users ──1:N── parent_settings
mistake_records ──1:N── mistake_reviews
mistake_records ──1:1── draft_papers
covenants ──1:N── covenant_signatures
community_posts ──1:N── post_replies
articles ──1:N── article_bookmarks
```

---

## 1. users - 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(50) | NOT NULL | 用户名(孩子或家长昵称) |
| role | VARCHAR(10) | NOT NULL, CHECK IN ('child','parent') | 角色 |
| grade | SMALLINT | NULL, CHECK 1-6 | 物理年级(仅child) |
| avatar_url | VARCHAR(255) | NULL | 头像URL |
| parent_id | UUID | FK -> users.id, NULL | 关联家长(仅child) |
| sunlight_points | INT | DEFAULT 0 | 累计阳光值 |
| streak_days | INT | DEFAULT 0 | 连续打卡天数 |
| is_onboarded | BOOLEAN | DEFAULT false | 是否完成注册评估 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

索引: `idx_users_parent_id`, `idx_users_role_grade`

---

## 2. assessments - 执行功能评估表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| focus_attention | SMALLINT | NOT NULL, CHECK 1-5 | 专注持久度评分 |
| organization | SMALLINT | NOT NULL, CHECK 1-5 | 物品整洁度评分 |
| emotional_control | SMALLINT | NOT NULL, CHECK 1-5 | 情绪克制力评分 |
| recommended_level | SMALLINT | NOT NULL, CHECK 1-5 | 推荐难度等级 |
| task_density | VARCHAR(20) | NOT NULL | 任务密度(low/medium/high) |
| source | VARCHAR(20) | DEFAULT 'initial' | 来源(initial/dynamic修正) |
| created_at | TIMESTAMP | DEFAULT NOW() | 评估时间 |

索引: `idx_assessments_user_id`, 同一用户可有多条评估(初始+动态修正)

---

## 3. tasks - 每日任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 任务标题 |
| description | TEXT | NULL | 任务描述 |
| type | VARCHAR(20) | NOT NULL, CHECK IN ('habit','game','organization','mistake_review','focus_exercise') | 任务类型 |
| status | VARCHAR(20) | DEFAULT 'pending', CHECK IN ('pending','completed','skipped') | 状态 |
| reward_points | SMALLINT | DEFAULT 10 | 奖励阳光值 |
| icon | VARCHAR(50) | NULL | 任务图标标识 |
| week_day | VARCHAR(10) | NULL | 对应星期 |
| assigned_date | DATE | NOT NULL | 分配日期 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| completion_photo_url | VARCHAR(255) | NULL | 完成拍照URL |
| sop_id | UUID | FK -> habit_sops.id, NULL | 关联SOP |

索引: `idx_tasks_user_date`, `idx_tasks_status`

---

## 4. habit_sops - 习惯标准操作程序表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| title | VARCHAR(100) | NOT NULL | SOP标题 |
| week_number | SMALLINT | NOT NULL | 周数 |
| grade_range | VARCHAR(10) | NOT NULL | 适用年级范围(如"1-2","3-4","5-6") |
| difficulty_level | SMALLINT | NOT NULL | 适配难度等级 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

---

## 5. sop_steps - SOP步骤表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| sop_id | UUID | FK -> habit_sops.id, NOT NULL | 关联SOP |
| order | SMALLINT | NOT NULL | 步骤顺序 |
| instruction | TEXT | NOT NULL | 步骤说明 |
| image_url | VARCHAR(255) | NULL | 示例图URL |
| gif_url | VARCHAR(255) | NULL | 示例GIF/视频URL |

---

## 6. mistake_records - 错题记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| subject | VARCHAR(30) | NOT NULL | 科目(math/chinese/english/science) |
| image_url | VARCHAR(255) | NOT NULL | 错题图片URL |
| recognized_text | TEXT | NULL | OCR识别文本 |
| is_carelessness | BOOLEAN | NOT NULL | 是否粗心(黄金一问结果) |
| category | VARCHAR(30) | NULL, CHECK IN (12类粗心分类) | 粗心分类 |
| knowledge_point | VARCHAR(100) | NULL | 知识点标记(知识漏洞时) |
| grade | SMALLINT | NOT NULL | 当前年级 |
| curriculum_chapter | VARCHAR(100) | NULL | 教材章节 |
| review_strategy | VARCHAR(30) | DEFAULT '3day-repeat' | 复习策略 |
| next_review_at | TIMESTAMP | NOT NULL | 下次复习时间 |
| review_count | SMALLINT | DEFAULT 0 | 已复习次数 |
| resolved | BOOLEAN | DEFAULT false | 是否已解决 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

索引: `idx_mistake_user_subject`, `idx_mistake_category`, `idx_mistake_next_review`

**12类粗心分类 (category CHECK)**:
- `symbol_error` 看错符号
- `unit_missing` 漏写单位
- `misread_details` 读题遗漏
- `copying_error` 抄写错误
- `skipped_step` 跳步计算
- `rushing` 急于求成
- `lost_focus` 注意力涣散
- `messy_writing` 书写混乱
- `format_error` 格式错误
- `spelling_slip` 笔误/拼写
- `wild_guess` 盲目猜测
- `something_else` 其他

---

## 7. mistake_reviews - 错题复习记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| mistake_id | UUID | FK -> mistake_records.id, NOT NULL | 关联错题 |
| can_resolve_now | BOOLEAN | NOT NULL | 本次能否独立做对 |
| confidence_level | SMALLINT | CHECK 1-5 | 信心等级 |
| reviewed_at | TIMESTAMP | DEFAULT NOW() | 复习时间 |
| next_review_at | TIMESTAMP | NULL | 间隔重复下次复习时间 |

---

## 8. draft_papers - 草稿纸表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| mistake_id | UUID | FK -> mistake_records.id, NOT NULL | 关联错题 |
| image_url | VARCHAR(255) | NOT NULL | 草稿纸图片URL |
| chaos_zones | JSONB | NULL | 检测到的混乱区域 [{x,y,width,height,severity}] |
| uploaded_at | TIMESTAMP | DEFAULT NOW() | 上传时间 |

---

## 9. item_loss_records - 物品丢失记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| item_name | VARCHAR(50) | NOT NULL | 物品名称 |
| lost_location | VARCHAR(30) | NOT NULL | 丢失地点(school/bus/home/playground/other) |
| estimated_cost | DECIMAL(10,2) | DEFAULT 0 | 估计金额损失 |
| lost_date | DATE | NOT NULL | 丢失日期 |
| frequency_30d | SMALLINT | DEFAULT 1 | 30天内丢失频次(自动计算) |
| is_high_frequency | BOOLEAN | DEFAULT false | 是否高频(30天>=3次) |
| suggestion | TEXT | NULL | 系统生成的急救建议 |
| created_at | TIMESTAMP | DEFAULT NOW() | 记录时间 |

索引: `idx_loss_user_item`, `idx_loss_frequency`

---

## 10. before_after_photos - 收纳前后对比表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| before_image_url | VARCHAR(255) | NOT NULL | 收纳前照片 |
| after_image_url | VARCHAR(255) | NOT NULL | 收纳后照片 |
| organization_score | SMALLINT | NULL | AI评分(1-10) |
| points_earned | SMALLINT | DEFAULT 15 | 获得阳光值 |
| uploaded_at | TIMESTAMP | DEFAULT NOW() | 上传时间 |

---

## 11. pomodoro_sessions - 番茄钟会话表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| subject | VARCHAR(30) | NOT NULL | 科目 |
| task_description | TEXT | NULL | 任务描述 |
| estimated_minutes | SMALLINT | NOT NULL | 预估用时 |
| actual_minutes | SMALLINT | NULL | 实际用时 |
| time_drain_reason | VARCHAR(30) | NULL | 耗时原因(reading/calculation/daydreaming) |
| start_time | TIMESTAMP | NOT NULL | 开始时间 |
| end_time | TIMESTAMP | NULL | 结束时间 |
| uncertain_count | SMALLINT | DEFAULT 0 | 不确定题目标记数 |
| status | VARCHAR(20) | DEFAULT 'running', CHECK IN ('running','completed','abandoned') | 状态 |

索引: `idx_pomodoro_user_date`

---

## 12. pomodoro_uncertain_marks - 不确定题目标记表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| session_id | UUID | FK -> pomodoro_sessions.id, NOT NULL | 关联会话 |
| question_number | SMALLINT | NULL | 题号 |
| subject | VARCHAR(30) | NULL | 科目 |
| auto_linked_mistake | BOOLEAN | DEFAULT false | 是否自动关联到错题本 |
| marked_at | TIMESTAMP | DEFAULT NOW() | 标记时间 |

---

## 13. growth_snapshots - 成长数据快照表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| snapshot_date | DATE | NOT NULL | 快照日期 |
| mistake_rate | DECIMAL(5,4) | NULL | 漏题率 |
| item_loss_rate | SMALLINT | NULL | 丢东西频次(月) |
| task_completion_rate | DECIMAL(5,4) | NULL | 任务完成率 |
| focus_score | SMALLINT | NULL | 专注评分 |
| neatness_score | SMALLINT | NULL | 整洁评分 |
| metacognition_score | SMALLINT | NULL | 元认知评分 |
| emotion_score | SMALLINT | NULL | 情绪评分 |
| source | VARCHAR(20) | DEFAULT 'daily' | 来源(daily/weekly/monthly) |

索引: `idx_growth_user_date`, UNIQUE(user_id, snapshot_date, source)

---

## 14. diagnostic_alerts - 诊断预警表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 标题(不使用警报/糟糕) |
| description | TEXT | NOT NULL | 描述 |
| suggestion | TEXT | NOT NULL | 建议措施 |
| severity | VARCHAR(20) | NOT NULL, CHECK IN ('info','warning','positive') | 严重程度 |
| related_metric | VARCHAR(50) | NULL | 关联指标 |
| metric_change | DECIMAL(5,2) | NULL | 指标变化百分比 |
| is_read | BOOLEAN | DEFAULT false | 是否已读 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

索引: `idx_alerts_user_severity`

---

## 15. badges - 勋章定义表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(50) | NOT NULL | 勋章名称 |
| description | TEXT | NOT NULL | 描述 |
| icon | VARCHAR(50) | NOT NULL | 图标标识 |
| color | VARCHAR(20) | NOT NULL | 颜色 |
| requirement | TEXT | NOT NULL | 解锁条件描述 |
| requirement_type | VARCHAR(30) | NOT NULL | 条件类型(streak_days/task_count/item_loss_zero/etc) |
| requirement_value | INT | NOT NULL | 条件数值 |
| reward_points | SMALLINT | DEFAULT 50 | 解锁奖励阳光值 |

---

## 16. badge_unlocks - 勋章解锁记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| badge_id | UUID | FK -> badges.id, NOT NULL | 关联勋章 |
| unlocked_at | TIMESTAMP | DEFAULT NOW() | 解锁时间 |

UNIQUE(user_id, badge_id)

---

## 17. covenants - 成长契约表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| child_id | UUID | FK -> users.id, NOT NULL | 关联孩子 |
| parent_id | UUID | FK -> users.id, NOT NULL | 关联家长 |
| goal | TEXT | NOT NULL | 契约目标 |
| reward | VARCHAR(100) | NOT NULL | 奖励描述 |
| reward_type | VARCHAR(20) | NOT NULL, CHECK IN ('experience','material','custom') | 奖励类型 |
| nudge_message | TEXT | NULL | 系统提示(防贿赂) |
| status | VARCHAR(20) | DEFAULT 'draft', CHECK IN ('draft','active','completed','expired') | 状态 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |

---

## 18. covenant_signatures - 契约签署表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| covenant_id | UUID | FK -> covenants.id, NOT NULL | 关联契约 |
| signer_id | UUID | FK -> users.id, NOT NULL | 签署人 |
| signer_role | VARCHAR(10) | NOT NULL | 角色(child/parent) |
| signature_data | TEXT | NULL | 手写签名数据(base64) |
| signed_at | TIMESTAMP | DEFAULT NOW() | 签署时间 |

UNIQUE(covenant_id, signer_role)

---

## 19. parent_settings - 家长设置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL, UNIQUE | 关联家长 |
| difficulty_level | SMALLINT | DEFAULT 2, CHECK 1-3 | 难度等级(1阳光/2微风/3挑战) |
| daily_reminder | BOOLEAN | DEFAULT true | 每日提醒 |
| achievement_notification | BOOLEAN | DEFAULT true | 成就通知 |
| weekly_report | BOOLEAN | DEFAULT true | 周报 |
| school_sync | BOOLEAN | DEFAULT false | 学校数据共享 |
| school_sync_code | VARCHAR(20) | NULL | 学校共享邀请码 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

---

## 20. community_posts - 社区帖子表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| author_id | UUID | FK -> users.id, NOT NULL | 作者(匿名化展示) |
| title | VARCHAR(200) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| tags | VARCHAR(100)[] | NULL | 标签数组 |
| reply_count | SMALLINT | DEFAULT 0 | 回复数 |
| like_count | SMALLINT | DEFAULT 0 | 点赞数 |
| has_expert_answer | BOOLEAN | DEFAULT false | 是否有专家回答 |
| is_anonymous | BOOLEAN | DEFAULT true | 是否匿名 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

索引: `idx_posts_tags`(GIN索引)

---

## 21. post_replies - 帖子回复表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| post_id | UUID | FK -> community_posts.id, NOT NULL | 关联帖子 |
| author_id | UUID | FK -> users.id, NOT NULL | 作者 |
| content | TEXT | NOT NULL | 回复内容 |
| is_expert | BOOLEAN | DEFAULT false | 是否专家回复 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

---

## 22. articles - 循证资源表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| summary | TEXT | NULL | 摘要 |
| content_url | VARCHAR(255) | NOT NULL | 内容URL |
| category | VARCHAR(30) | NOT NULL | 分类(executive_function/anxiety_cbt/time_management) |
| type | VARCHAR(20) | NOT NULL, CHECK IN ('article','video','cbt') | 类型 |
| reading_time_minutes | SMALLINT | NULL | 阅读时长 |
| image_url | VARCHAR(255) | NULL | 封面图 |
| author | VARCHAR(100) | NULL | 作者/专家 |
| published_at | TIMESTAMP | NOT NULL | 发布时间 |

索引: `idx_articles_category`

---

## 23. article_bookmarks - 文章收藏表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| article_id | UUID | FK -> articles.id, NOT NULL | 关联文章 |
| created_at | TIMESTAMP | DEFAULT NOW() | 收藏时间 |

UNIQUE(user_id, article_id)

---

## 24. shared_covenants - 共享契约表(社区)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| covenant_id | UUID | FK -> covenants.id, NOT NULL | 关联原始契约 |
| like_count | SMALLINT | DEFAULT 0 | 点赞数 |
| shared_at | TIMESTAMP | DEFAULT NOW() | 分享时间 |

---

## 25. growth_reports - 生成报告表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| period | VARCHAR(20) | NOT NULL | 时间范围(semester/year/all) |
| pdf_url | VARCHAR(255) | NOT NULL | PDF URL |
| include_peer_comparison | BOOLEAN | DEFAULT true | 是否含同龄对比 |
| generated_at | TIMESTAMP | DEFAULT NOW() | 生成时间 |

---

## 26. task_weekly_progress - 每周打卡进度表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK -> users.id, NOT NULL | 关联用户 |
| week_number | SMALLINT | NOT NULL | 周数 |
| year | SMALLINT | NOT NULL | 年份 |
| completed_days | SMALLINT | DEFAULT 0 | 完成天数 |
| total_days | SMALLINT | DEFAULT 7 | 总天数 |
| progress_percent | DECIMAL(5,2) | DEFAULT 0 | 完成百分比 |
| habit_id | UUID | FK -> habit_sops.id | 关联本周习惯 |

UNIQUE(user_id, year, week_number)