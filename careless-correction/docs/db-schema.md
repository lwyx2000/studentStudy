# 小树成长岛 - 数据库表结构文档

> 版本: v2.0 | 基线日期: 2026-06-15 | 数据库: SQLite
>
> **命名约定:**
> - 表名: `t_` 前缀 (如 `t_users`)
> - 主键: `pk_` + 去掉 `t_` 的表名 (如 `pk_users`)
> - 外键: `fk_` + 去掉 `t_` 的被引用表名 (如 `fk_users`)
> - 主键类型: INT AUTO_INCREMENT（SQLite 自增）

---

## ER 关系概览

```
t_users ──1:N── t_assessments
t_users ──1:N── t_tasks
t_tasks  ──1:N── t_sub_tasks
t_users ──1:N── t_mistake_records
t_users ──1:N── t_item_loss_records
t_users ──1:N── t_item_storage_records
t_users ──1:N── t_badge_unlocks
t_users ──1:N── t_growth_snapshots
t_users ──1:N── t_diagnostic_alerts
t_users ──1:N── t_parent_settings
t_users ──1:N── t_sunlight_history
t_users ──1:N── t_apple_history
t_users ──1:N── t_check_ins
t_users ──1:1── t_llm_config
t_habit_sops ──1:N── t_sop_steps
t_habit_sops ──1:N── t_users (fk_users)
t_mistake_records ──1:N── t_mistake_reviews
t_articles ──1:N── t_article_bookmarks
```

---

## 1. t_users - 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_users | INTEGER | PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(50) | NOT NULL | 用户名(孩子或家长昵称) |
| login_name | VARCHAR(50) | UNIQUE, NULL | 登录名(孩子的拼音首字母) |
| role | VARCHAR(10) | NOT NULL | 角色(child/parent) |
| password_hash | VARCHAR(255) | NULL | 密码哈希 |
| grade | SMALLINT | NULL | 物理年级(0=幼儿园,1-6=小学,7-9=初中,10-12=高中) |
| avatar_url | VARCHAR(255) | NULL | 头像URL |
| fk_users_parent | INTEGER | FK -> t_users.pk_users, NULL | 关联家长(仅child) |
| sunlight_points | INTEGER | DEFAULT 0 | 累计阳光值 |
| apples | INTEGER | DEFAULT 0 | 累计苹果数(可兑换现金奖励) |
| streak_days | INTEGER | DEFAULT 0 | 连续打卡天数 |
| is_onboarded | BOOLEAN | DEFAULT false | 是否完成注册评估 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() | 更新时间 |

---

## 2. t_assessments - 执行功能评估表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_assessments | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| focus_attention | SMALLINT | NOT NULL, 1-5 | 专注持久度评分 |
| organization | SMALLINT | NOT NULL, 1-5 | 物品整洁度评分 |
| emotional_control | SMALLINT | NOT NULL, 1-5 | 情绪克制力评分 |
| planning | SMALLINT | NOT NULL, 1-5 | 计划启动力评分 |
| impulse_control | SMALLINT | NOT NULL, 1-5 | 冲动抑制力评分 |
| recommended_level | SMALLINT | NOT NULL, 1-5 | 推荐难度等级 |
| task_density | VARCHAR(20) | NOT NULL | 任务密度(low/medium/high) |
| source | VARCHAR(20) | DEFAULT 'initial' | 来源(initial/dynamic) |
| created_at | DATETIME | DEFAULT NOW() | 评估时间 |

---

## 3. t_tasks - 每日任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_tasks | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 任务标题 |
| description | TEXT | NULL | 任务描述 |
| type | VARCHAR(20) | NOT NULL | 类型(morning_routine/study_habit/life_skill/exercise/reflection) |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态(pending/completed/skipped) |
| reward_points | SMALLINT | DEFAULT 10 | 奖励阳光值 |
| icon | VARCHAR(50) | NULL | 任务图标 |
| week_day | VARCHAR(50) | NULL | 对应星期(逗号分隔) |
| assigned_date | DATE | NOT NULL | 分配日期 |
| completed_at | DATETIME | NULL | 完成时间 |
| completion_photo_url | VARCHAR(255) | NULL | 完成拍照URL |
| fk_habit_sops | INTEGER | FK -> t_habit_sops.pk_habit_sops, NULL | 关联SOP |
| active | BOOLEAN | DEFAULT true | 是否活跃(软删除标记) |

---

## 4. t_sub_tasks - 子任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_sub_tasks | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_tasks | INTEGER | FK -> t_tasks.pk_tasks, NOT NULL, CASCADE | 关联任务 |
| title | VARCHAR(100) | NOT NULL | 子任务标题 |
| type | VARCHAR(20) | NOT NULL | 子任务类别 |
| week_day | VARCHAR(50) | NULL | 适用日(weekday/weekend/逗号分隔) |
| sort_order | SMALLINT | DEFAULT 0 | 排序序号 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

## 5. t_habit_sops - 习惯标准操作程序表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_habit_sops | INTEGER | PK, AUTO_INCREMENT | 主键 |
| title | VARCHAR(100) | NOT NULL | SOP标题 |
| grade_range | VARCHAR(10) | NOT NULL | 适用年级范围 |
| difficulty_level | SMALLINT | NOT NULL | 适配难度等级 |
| reward_points | SMALLINT | DEFAULT 5 | 奖励阳光值 |
| active | BOOLEAN | DEFAULT true | 是否活跃(软删除标记) |
| fk_users | INTEGER | FK -> t_users.pk_users, NULL | 关联用户(家长) |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

## 6. t_sop_steps - SOP 步骤表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_sop_steps | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_habit_sops | INTEGER | FK -> t_habit_sops.pk_habit_sops, NOT NULL | 关联SOP |
| order | SMALLINT | NOT NULL | 步骤顺序 |
| instruction | TEXT | NOT NULL | 步骤说明 |
| image_url | VARCHAR(255) | NULL | 示例图URL |
| gif_url | VARCHAR(255) | NULL | 示例GIF/视频URL |

---

## 7. t_mistake_records - 错题记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_mistake_records | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| subject | VARCHAR(30) | NOT NULL | 科目 |
| image_url | VARCHAR(255) | NOT NULL | 错题图片URL |
| recognized_text | TEXT | NULL | OCR识别文本 |
| is_carelessness | BOOLEAN | DEFAULT true | 是否粗心 |
| category | VARCHAR(30) | NULL | 粗心分类(12类) |
| knowledge_point | VARCHAR(100) | NULL | 知识点标记 |
| grade | SMALLINT | NULL | 当前年级 |
| curriculum_chapter | VARCHAR(100) | NULL | 教材章节 |
| review_strategy | VARCHAR(30) | DEFAULT '3day-repeat' | 复习策略 |
| next_review_at | DATETIME | NOT NULL | 下次复习时间 |
| review_count | SMALLINT | DEFAULT 0 | 已复习次数 |
| resolved | BOOLEAN | DEFAULT false | 是否已解决 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

**12类粗心分类**: symbol_error, unit_missing, misread_details, copying_error, skipped_step, rushing, lost_focus, messy_writing, format_error, spelling_slip, wild_guess, something_else

---

## 8. t_mistake_reviews - 错题复习记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_mistake_reviews | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_mistake_records | INTEGER | FK -> t_mistake_records.pk_mistake_records, NOT NULL | 关联错题 |
| can_resolve_now | BOOLEAN | NOT NULL | 能否独立做对 |
| confidence_level | SMALLINT | NULL, 1-5 | 信心等级 |
| reviewed_at | DATETIME | DEFAULT NOW() | 复习时间 |
| next_review_at | DATETIME | NULL | 下次复习时间 |

---

## 9. t_item_storage_records - 物品收纳记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_item_storage_records | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| item_name | VARCHAR(50) | NOT NULL | 物品名称 |
| storage_location | VARCHAR(100) | NOT NULL | 收纳位置 |
| notes | TEXT | NULL | 备注 |
| storage_date | DATE | NOT NULL | 收纳日期 |
| created_at | DATETIME | DEFAULT NOW() | 记录时间 |

---

## 10. t_item_loss_records - 物品丢失记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_item_loss_records | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| item_name | VARCHAR(50) | NOT NULL | 物品名称 |
| lost_location | VARCHAR(30) | NOT NULL | 丢失地点 |
| estimated_cost | DECIMAL(10,2) | DEFAULT 0 | 估计金额损失 |
| lost_date | DATE | NOT NULL | 丢失日期 |
| frequency_30d | SMALLINT | DEFAULT 1 | 30天丢失频次 |
| is_high_frequency | BOOLEAN | DEFAULT false | 是否高频(>=3次) |
| suggestion | TEXT | NULL | 急救建议 |
| created_at | DATETIME | DEFAULT NOW() | 记录时间 |

---

## 11. t_reward_items - 阳光值兑换物品表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_reward_items | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联家长 |
| name | VARCHAR(100) | NOT NULL | 物品名称 |
| description | TEXT | NULL | 描述 |
| cost | SMALLINT | NOT NULL | 所需阳光值 |
| icon | VARCHAR(20) | NULL | 图标 |
| active | BOOLEAN | DEFAULT true | 是否可用 |

---

## 12. t_sunlight_history - 阳光值变动记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_sunlight_history | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| amount | INTEGER | NOT NULL | 变动值(正=获得,负=消费) |
| reason | VARCHAR(200) | NOT NULL | 变动原因 |
| type | VARCHAR(10) | NOT NULL | 类型(earn/spend) |
| created_at | DATETIME | DEFAULT NOW() | 变动时间 |

---

## 13. t_check_ins - 打卡审批记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_check_ins | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| check_date | VARCHAR(20) | NOT NULL | 打卡日期 |
| total_points | INTEGER | DEFAULT 0 | 累计阳光值 |
| habit_step_count | INTEGER | DEFAULT 0 | 习惯步骤数 |
| task_count | INTEGER | DEFAULT 0 | 任务数 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态(pending/approved/rejected) |
| created_at | DATETIME | DEFAULT NOW() | 提交时间 |
| approved_at | DATETIME | NULL | 审批时间 |

---

## 14. t_llm_config - 大模型配置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_llm_config | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL, UNIQUE | 关联家长 |
| endpoint | VARCHAR(255) | NOT NULL | API 地址 |
| api_key | VARCHAR(255) | NOT NULL | API Key |
| model | VARCHAR(50) | NOT NULL | 模型名称 |
| mistake_prompt | TEXT | NOT NULL | 错题分析 prompt |
| assessment_prompt | TEXT | NOT NULL | 成长评估 prompt |
| assessment_cron | VARCHAR(10) | DEFAULT 'weekly' | 评估周期 |
| enabled | BOOLEAN | DEFAULT false | 是否启用 |
| updated_at | DATETIME | DEFAULT NOW() | 更新时间 |

---

## 15. t_growth_snapshots - 成长数据快照表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_growth_snapshots | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| snapshot_date | DATE | NOT NULL | 快照日期 |
| mistake_rate | DECIMAL(5,4) | NULL | 漏题率 |
| item_loss_rate | SMALLINT | NULL | 丢失频次(月) |
| task_completion_rate | DECIMAL(5,4) | NULL | 任务完成率 |
| focus_score | SMALLINT | NULL | 专注评分 |
| neatness_score | SMALLINT | NULL | 整洁评分 |
| metacognition_score | SMALLINT | NULL | 元认知评分 |
| emotion_score | SMALLINT | NULL | 情绪评分 |
| source | VARCHAR(20) | DEFAULT 'daily' | 来源(daily/weekly/monthly) |

---

## 16. t_diagnostic_alerts - 诊断预警表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_diagnostic_alerts | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| title | VARCHAR(100) | NOT NULL | 标题 |
| description | TEXT | NOT NULL | 描述 |
| suggestion | TEXT | NOT NULL | 建议措施 |
| severity | VARCHAR(20) | NOT NULL | 程度(info/warning/positive) |
| related_metric | VARCHAR(50) | NULL | 关联指标 |
| metric_change | DECIMAL(5,2) | NULL | 指标变化 |
| is_read | BOOLEAN | DEFAULT false | 是否已读 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

## 17. t_badges - 勋章定义表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_badges | INTEGER | PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(50) | NOT NULL | 勋章名称 |
| description | TEXT | NOT NULL | 描述 |
| icon | VARCHAR(50) | NOT NULL | 图标 |
| color | VARCHAR(20) | NOT NULL | 颜色 |
| requirement | TEXT | NOT NULL | 解锁条件 |
| requirement_type | VARCHAR(30) | NOT NULL | 条件类型 |
| requirement_value | INTEGER | NOT NULL | 条件数值 |
| reward_points | SMALLINT | DEFAULT 50 | 解锁奖励阳光值 |

---

## 18. t_badge_unlocks - 勋章解锁记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_badge_unlocks | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| fk_badges | INTEGER | FK -> t_badges.pk_badges, NOT NULL | 关联勋章 |
| unlocked_at | DATETIME | DEFAULT NOW() | 解锁时间 |

UNIQUE(fk_users, fk_badges)

---

## 19. t_apple_history - 苹果变动记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_apple_history | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| amount | INTEGER | NOT NULL | 变动值(正=获得,负=消费) |
| reason | VARCHAR(200) | NOT NULL | 变动原因 |
| type | VARCHAR(10) | NOT NULL | 类型(grow/redeem) |
| created_at | DATETIME | DEFAULT NOW() | 变动时间 |

---

## 20. t_parent_settings - 家长设置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_parent_settings | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL, UNIQUE | 关联家长 |
| daily_reminder | BOOLEAN | DEFAULT true | 每日提醒 |
| achievement_notification | BOOLEAN | DEFAULT true | 成就通知 |
| weekly_report | BOOLEAN | DEFAULT true | 周报 |
| school_sync | BOOLEAN | DEFAULT false | 数据共享 |
| school_sync_code | VARCHAR(20) | NULL | 共享邀请码 |
| updated_at | DATETIME | DEFAULT NOW() | 更新时间 |

---

## 21. t_articles - 循证资源表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_articles | INTEGER | PK, AUTO_INCREMENT | 主键 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| summary | TEXT | NULL | 摘要 |
| content_url | VARCHAR(255) | NOT NULL | 内容URL |
| category | VARCHAR(30) | NOT NULL | 分类 |
| type | VARCHAR(20) | NOT NULL | 类型(article/video/cbt) |
| reading_time_minutes | SMALLINT | NULL | 阅读时长 |
| image_url | VARCHAR(255) | NULL | 封面图 |
| author | VARCHAR(100) | NULL | 作者 |
| published_at | DATETIME | NOT NULL | 发布时间 |

---

## 22. t_article_bookmarks - 文章收藏表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_article_bookmarks | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| fk_articles | INTEGER | FK -> t_articles.pk_articles, NOT NULL | 关联文章 |
| created_at | DATETIME | DEFAULT NOW() | 收藏时间 |

UNIQUE(fk_users, fk_articles)

---

## 23. t_growth_reports - 生成报告表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_growth_reports | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| period | VARCHAR(20) | NOT NULL | 时间范围 |
| pdf_url | VARCHAR(255) | NOT NULL | PDF URL |
| include_peer_comparison | BOOLEAN | DEFAULT true | 同龄对比 |
| generated_at | DATETIME | DEFAULT NOW() | 生成时间 |

---

## 24. t_task_weekly_progress - 每周打卡进度表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pk_task_weekly_progress | INTEGER | PK, AUTO_INCREMENT | 主键 |
| fk_users | INTEGER | FK -> t_users.pk_users, NOT NULL | 关联用户 |
| week_number | SMALLINT | NOT NULL | 周数 |
| year | SMALLINT | NOT NULL | 年份 |
| completed_days | SMALLINT | DEFAULT 0 | 完成天数 |
| total_days | SMALLINT | DEFAULT 7 | 总天数 |
| progress_percent | DECIMAL(5,2) | DEFAULT 0 | 完成百分比 |
| fk_habit_sops | INTEGER | FK -> t_habit_sops.pk_habit_sops, NULL | 关联习惯 |

UNIQUE(fk_users, year, week_number)