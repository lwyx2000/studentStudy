-- 全小学阶段儿童粗心矫正系统 - MySQL 数据库初始化脚本
-- MySQL 8.0+

CREATE TABLE IF NOT EXISTS t_users (
  pk_users INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  name VARCHAR(50) NOT NULL COMMENT '用户名(孩子或家长昵称)',
  role VARCHAR(10) NOT NULL COMMENT '角色: child=孩子, parent=家长',
  password_hash VARCHAR(255) NULL COMMENT '密码哈希(仅家长账号)',
  grade TINYINT COMMENT '物理年级(仅child, 0=幼儿园,1-6=小学,7-9=初中,10-12=高中)',
  avatar_url VARCHAR(255) COMMENT '头像URL',
  fk_users_parent INT COMMENT '关联家长(仅child)',
  sunlight_points INT DEFAULT 0 COMMENT '累计阳光值',
  streak_days INT DEFAULT 0 COMMENT '连续打卡天数',
  is_onboarded TINYINT(1) DEFAULT 0 COMMENT '是否完成注册评估',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT chk_users_role CHECK (role IN ('child', 'parent')),
  CONSTRAINT fk_users_parent FOREIGN KEY (fk_users_parent) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE IF NOT EXISTS t_assessments (
  pk_assessments INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  focus_attention TINYINT NOT NULL COMMENT '专注持久度评分(1-5)',
  organization TINYINT NOT NULL COMMENT '物品整洁度评分(1-5)',
  emotional_control TINYINT NOT NULL COMMENT '情绪克制力评分(1-5)',
  planning TINYINT NOT NULL COMMENT '计划启动力评分(1-5)',
  impulse_control TINYINT NOT NULL COMMENT '冲动抑制力评分(1-5)',
  recommended_level TINYINT NOT NULL COMMENT '推荐难度等级(1-5)',
  task_density VARCHAR(20) NOT NULL COMMENT '任务密度: low/medium/high',
  source VARCHAR(20) DEFAULT 'initial' COMMENT '来源: initial=初始, dynamic=动态修正',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '评估时间',
  CONSTRAINT chk_assessments_focus CHECK (focus_attention BETWEEN 1 AND 5),
  CONSTRAINT chk_assessments_org CHECK (organization BETWEEN 1 AND 5),
  CONSTRAINT chk_assessments_emotion CHECK (emotional_control BETWEEN 1 AND 5),
  CONSTRAINT chk_assessments_plan CHECK (planning BETWEEN 1 AND 5),
  CONSTRAINT chk_assessments_impulse CHECK (impulse_control BETWEEN 1 AND 5),
  CONSTRAINT chk_assessments_level CHECK (recommended_level BETWEEN 1 AND 5),
  CONSTRAINT fk_assessments_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='执行功能评估表';

CREATE TABLE IF NOT EXISTS t_habit_sops (
  pk_habit_sops INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  title VARCHAR(100) NOT NULL COMMENT 'SOP标题',
  week_number TINYINT NOT NULL COMMENT '周数',
  grade_range VARCHAR(10) NOT NULL COMMENT '适用年级范围(如1-2,3-4,5-6)',
  difficulty_level TINYINT NOT NULL COMMENT '适配难度等级',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='习惯标准操作程序表';

CREATE TABLE IF NOT EXISTS t_sop_steps (
  pk_sop_steps INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_habit_sops INT NOT NULL COMMENT '关联SOP',
  `order` TINYINT NOT NULL COMMENT '步骤顺序',
  instruction TEXT NOT NULL COMMENT '步骤说明',
  image_url VARCHAR(255) COMMENT '示例图URL',
  gif_url VARCHAR(255) COMMENT '示例GIF/视频URL',
  CONSTRAINT fk_sop_steps_habit FOREIGN KEY (fk_habit_sops) REFERENCES t_habit_sops(pk_habit_sops) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SOP步骤表';

CREATE TABLE IF NOT EXISTS t_tasks (
  pk_tasks INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  title VARCHAR(100) NOT NULL COMMENT '任务标题',
  description TEXT COMMENT '任务描述',
  type VARCHAR(20) NOT NULL COMMENT '任务类型: morning_routine/study_habit/life_skill/exercise/reflection',
  status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/completed/skipped',
  reward_points TINYINT DEFAULT 10 COMMENT '奖励阳光值',
  icon VARCHAR(50) COMMENT '任务图标标识',
  week_day VARCHAR(10) COMMENT '对应星期',
  assigned_date DATE NOT NULL COMMENT '分配日期',
  completed_at TIMESTAMP NULL COMMENT '完成时间',
  completion_photo_url VARCHAR(255) COMMENT '完成拍照URL',
  fk_habit_sops INT COMMENT '关联SOP',
  CONSTRAINT chk_tasks_type CHECK (type IN ('morning_routine','study_habit','life_skill','exercise','reflection')),
  CONSTRAINT chk_tasks_status CHECK (status IN ('pending','completed','skipped')),
  CONSTRAINT fk_tasks_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT fk_tasks_habit FOREIGN KEY (fk_habit_sops) REFERENCES t_habit_sops(pk_habit_sops)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日任务表';

CREATE TABLE IF NOT EXISTS t_mistake_records (
  pk_mistake_records INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  subject VARCHAR(30) NOT NULL COMMENT '科目: math/chinese/english/science',
  image_url VARCHAR(255) NOT NULL COMMENT '错题图片URL',
  recognized_text TEXT COMMENT 'OCR识别文本',
  is_carelessness TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否粗心(黄金一问结果)',
  category VARCHAR(30) COMMENT '粗心分类: symbol_error/unit_missing等12类',
  knowledge_point VARCHAR(100) COMMENT '知识点标记(知识漏洞时)',
  grade TINYINT COMMENT '当前年级',
  curriculum_chapter VARCHAR(100) COMMENT '教材章节',
  review_strategy VARCHAR(30) DEFAULT '3day-repeat' COMMENT '复习策略: 3day-repeat/weekly-repeat/monthly',
  next_review_at TIMESTAMP NOT NULL COMMENT '下次复习时间',
  review_count TINYINT DEFAULT 0 COMMENT '已复习次数',
  resolved TINYINT(1) DEFAULT 0 COMMENT '是否已解决',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT chk_mistakes_category CHECK (category IN (
    'symbol_error','unit_missing','misread_details','copying_error',
    'skipped_step','rushing','lost_focus','messy_writing',
    'format_error','spelling_slip','wild_guess','something_else'
  )),
  CONSTRAINT fk_mistakes_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错题记录表';

CREATE TABLE IF NOT EXISTS t_mistake_reviews (
  pk_mistake_reviews INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_mistake_records INT NOT NULL COMMENT '关联错题',
  can_resolve_now TINYINT(1) NOT NULL COMMENT '本次能否独立做对',
  confidence_level TINYINT COMMENT '信心等级(1-5)',
  reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '复习时间',
  next_review_at TIMESTAMP NULL COMMENT '间隔重复下次复习时间',
  CONSTRAINT chk_reviews_confidence CHECK (confidence_level BETWEEN 1 AND 5),
  CONSTRAINT fk_reviews_mistake FOREIGN KEY (fk_mistake_records) REFERENCES t_mistake_records(pk_mistake_records) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错题复习记录表';

CREATE TABLE IF NOT EXISTS t_item_storage_records (
  pk_item_storage_records INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  item_name VARCHAR(50) NOT NULL COMMENT '物品名称',
  storage_location VARCHAR(100) NOT NULL COMMENT '收纳位置',
  notes TEXT COMMENT '备注',
  storage_date DATE NOT NULL COMMENT '收纳日期',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  CONSTRAINT fk_storage_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物品收纳记录表';

CREATE TABLE IF NOT EXISTS t_item_loss_records (
  pk_item_loss_records INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  item_name VARCHAR(50) NOT NULL COMMENT '物品名称',
  lost_location VARCHAR(30) NOT NULL COMMENT '丢失地点: school/bus/home/playground/other',
  estimated_cost DECIMAL(10,2) DEFAULT 0 COMMENT '估计金额损失',
  lost_date DATE NOT NULL COMMENT '丢失日期',
  frequency_30d TINYINT DEFAULT 1 COMMENT '30天内丢失频次(自动计算)',
  is_high_frequency TINYINT(1) DEFAULT 0 COMMENT '是否高频(30天>=3次)',
  suggestion TEXT COMMENT '系统生成的急救建议',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  CONSTRAINT fk_loss_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物品丢失记录表';

CREATE TABLE IF NOT EXISTS t_reward_items (
  pk_reward_items INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联家长',
  name VARCHAR(100) NOT NULL COMMENT '物品名称',
  description TEXT COMMENT '描述',
  cost TINYINT NOT NULL COMMENT '所需阳光值',
  icon VARCHAR(20) COMMENT '图标emoji',
  active TINYINT(1) DEFAULT 1 COMMENT '是否可用',
  CONSTRAINT fk_reward_items_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阳光值兑换物品表';

CREATE TABLE IF NOT EXISTS t_sunlight_history (
  pk_sunlight_history INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  amount INT NOT NULL COMMENT '变动值(正=获得,负=消费)',
  reason VARCHAR(200) NOT NULL COMMENT '变动原因',
  type VARCHAR(10) NOT NULL COMMENT '类型: earn=获得, spend=消费',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '变动时间',
  CONSTRAINT chk_sunlight_type CHECK (type IN ('earn', 'spend')),
  CONSTRAINT fk_sunlight_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='阳光值变动记录表';

CREATE TABLE IF NOT EXISTS t_llm_config (
  pk_llm_config INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联家长',
  endpoint VARCHAR(255) NOT NULL COMMENT 'API地址',
  api_key VARCHAR(255) NOT NULL COMMENT 'API Key(加密存储)',
  model VARCHAR(50) NOT NULL COMMENT '模型名称',
  mistake_prompt TEXT NOT NULL COMMENT '错题分析prompt',
  assessment_prompt TEXT NOT NULL COMMENT '成长评估prompt',
  assessment_cron VARCHAR(10) DEFAULT 'weekly' COMMENT '评估周期: daily/weekly/monthly',
  enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT chk_llm_cron CHECK (assessment_cron IN ('daily', 'weekly', 'monthly')),
  CONSTRAINT fk_llm_config_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT uq_llm_config_user UNIQUE (fk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='大模型配置表';

CREATE TABLE IF NOT EXISTS t_growth_snapshots (
  pk_growth_snapshots INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  snapshot_date DATE NOT NULL COMMENT '快照日期',
  mistake_rate DECIMAL(5,4) COMMENT '漏题率',
  item_loss_rate TINYINT COMMENT '丢东西频次(月)',
  task_completion_rate DECIMAL(5,4) COMMENT '任务完成率',
  focus_score TINYINT COMMENT '专注评分',
  neatness_score TINYINT COMMENT '整洁评分',
  metacognition_score TINYINT COMMENT '元认知评分',
  emotion_score TINYINT COMMENT '情绪评分',
  source VARCHAR(20) DEFAULT 'daily' COMMENT '来源: daily/weekly/monthly',
  CONSTRAINT fk_growth_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT uq_growth_snapshot UNIQUE (fk_users, snapshot_date, source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成长数据快照表';

CREATE TABLE IF NOT EXISTS t_diagnostic_alerts (
  pk_diagnostic_alerts INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  title VARCHAR(100) NOT NULL COMMENT '标题(不使用警报/糟糕类词汇)',
  description TEXT NOT NULL COMMENT '描述',
  suggestion TEXT NOT NULL COMMENT '建议措施',
  severity VARCHAR(20) NOT NULL COMMENT '严重程度: info/warning/positive',
  related_metric VARCHAR(50) COMMENT '关联指标',
  metric_change DECIMAL(5,2) COMMENT '指标变化百分比',
  is_read TINYINT(1) DEFAULT 0 COMMENT '是否已读',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT chk_alerts_severity CHECK (severity IN ('info', 'warning', 'positive')),
  CONSTRAINT fk_alerts_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='诊断预警表';

CREATE TABLE IF NOT EXISTS t_badges (
  pk_badges INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  name VARCHAR(50) NOT NULL COMMENT '勋章名称',
  description TEXT NOT NULL COMMENT '描述',
  icon VARCHAR(50) NOT NULL COMMENT '图标标识',
  color VARCHAR(20) NOT NULL COMMENT '颜色',
  requirement TEXT NOT NULL COMMENT '解锁条件描述',
  requirement_type VARCHAR(30) NOT NULL COMMENT '条件类型: streak_days/task_count/item_loss_zero等',
  requirement_value INT NOT NULL COMMENT '条件数值',
  reward_points TINYINT DEFAULT 50 COMMENT '解锁奖励阳光值'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='勋章定义表';

CREATE TABLE IF NOT EXISTS t_badge_unlocks (
  pk_badge_unlocks INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  fk_badges INT NOT NULL COMMENT '关联勋章',
  unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '解锁时间',
  CONSTRAINT fk_badge_unlocks_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT fk_badge_unlocks_badge FOREIGN KEY (fk_badges) REFERENCES t_badges(pk_badges) ON DELETE CASCADE,
  CONSTRAINT uq_badge_unlocks UNIQUE (fk_users, fk_badges)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='勋章解锁记录表';

CREATE TABLE IF NOT EXISTS t_covenants (
  pk_covenants INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users_child INT NOT NULL COMMENT '关联孩子',
  fk_users_parent INT NOT NULL COMMENT '关联家长',
  goal TEXT NOT NULL COMMENT '契约目标',
  reward VARCHAR(100) NOT NULL COMMENT '奖励描述',
  reward_type VARCHAR(20) NOT NULL COMMENT '奖励类型: experience/material/custom',
  nudge_message TEXT COMMENT '系统提示(防贿赂引导语)',
  status VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft/active/completed/expired',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  completed_at TIMESTAMP NULL COMMENT '完成时间',
  CONSTRAINT chk_covenants_reward_type CHECK (reward_type IN ('experience', 'material', 'custom')),
  CONSTRAINT chk_covenants_status CHECK (status IN ('draft', 'active', 'completed', 'expired')),
  CONSTRAINT fk_covenants_child FOREIGN KEY (fk_users_child) REFERENCES t_users(pk_users),
  CONSTRAINT fk_covenants_parent FOREIGN KEY (fk_users_parent) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成长契约表';

CREATE TABLE IF NOT EXISTS t_covenant_signatures (
  pk_covenant_signatures INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_covenants INT NOT NULL COMMENT '关联契约',
  fk_users_signer INT NOT NULL COMMENT '签署人',
  signer_role VARCHAR(10) NOT NULL COMMENT '角色: child/parent',
  signature_data TEXT COMMENT '手写签名数据(base64)',
  signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '签署时间',
  CONSTRAINT fk_signatures_covenant FOREIGN KEY (fk_covenants) REFERENCES t_covenants(pk_covenants) ON DELETE CASCADE,
  CONSTRAINT fk_signatures_user FOREIGN KEY (fk_users_signer) REFERENCES t_users(pk_users),
  CONSTRAINT uq_covenant_signature UNIQUE (fk_covenants, signer_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='契约签署表';

CREATE TABLE IF NOT EXISTS t_parent_settings (
  pk_parent_settings INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联家长',
  difficulty_level TINYINT DEFAULT 2 COMMENT '难度等级: 1=阳光/2=微风/3=挑战',
  daily_reminder TINYINT(1) DEFAULT 1 COMMENT '每日提醒',
  achievement_notification TINYINT(1) DEFAULT 1 COMMENT '成就通知',
  weekly_report TINYINT(1) DEFAULT 1 COMMENT '周报',
  school_sync TINYINT(1) DEFAULT 0 COMMENT '学校数据共享',
  school_sync_code VARCHAR(20) COMMENT '学校共享邀请码',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT chk_parent_settings_level CHECK (difficulty_level BETWEEN 1 AND 3),
  CONSTRAINT fk_parent_settings_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT uq_parent_settings_user UNIQUE (fk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家长设置表';

CREATE TABLE IF NOT EXISTS t_community_posts (
  pk_community_posts INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users_author INT NOT NULL COMMENT '作者(匿名化展示)',
  title VARCHAR(200) NOT NULL COMMENT '标题',
  content TEXT NOT NULL COMMENT '内容',
  tags JSON COMMENT '标签数组',
  reply_count TINYINT DEFAULT 0 COMMENT '回复数',
  like_count TINYINT DEFAULT 0 COMMENT '点赞数',
  has_expert_answer TINYINT(1) DEFAULT 0 COMMENT '是否有专家回答',
  is_anonymous TINYINT(1) DEFAULT 1 COMMENT '是否匿名',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_posts_author FOREIGN KEY (fk_users_author) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区帖子表';

CREATE TABLE IF NOT EXISTS t_post_replies (
  pk_post_replies INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_community_posts INT NOT NULL COMMENT '关联帖子',
  fk_users_author INT NOT NULL COMMENT '作者',
  content TEXT NOT NULL COMMENT '回复内容',
  is_expert TINYINT(1) DEFAULT 0 COMMENT '是否专家回复',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_replies_post FOREIGN KEY (fk_community_posts) REFERENCES t_community_posts(pk_community_posts) ON DELETE CASCADE,
  CONSTRAINT fk_replies_author FOREIGN KEY (fk_users_author) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子回复表';

CREATE TABLE IF NOT EXISTS t_articles (
  pk_articles INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  title VARCHAR(200) NOT NULL COMMENT '标题',
  summary TEXT COMMENT '摘要',
  content_url VARCHAR(255) NOT NULL COMMENT '内容URL',
  category VARCHAR(30) NOT NULL COMMENT '分类: executive_function/anxiety_cbt/time_management',
  type VARCHAR(20) NOT NULL COMMENT '类型: article=文章/video=视频/cbt=认知训练',
  reading_time_minutes TINYINT COMMENT '阅读时长(分钟)',
  image_url VARCHAR(255) COMMENT '封面图',
  author VARCHAR(100) COMMENT '作者/专家',
  published_at TIMESTAMP NOT NULL COMMENT '发布时间',
  CONSTRAINT chk_articles_type CHECK (type IN ('article', 'video', 'cbt'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='循证资源表';

CREATE TABLE IF NOT EXISTS t_article_bookmarks (
  pk_article_bookmarks INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  fk_articles INT NOT NULL COMMENT '关联文章',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  CONSTRAINT fk_bookmarks_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT fk_bookmarks_article FOREIGN KEY (fk_articles) REFERENCES t_articles(pk_articles) ON DELETE CASCADE,
  CONSTRAINT uq_article_bookmarks UNIQUE (fk_users, fk_articles)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章收藏表';

CREATE TABLE IF NOT EXISTS t_shared_covenants (
  pk_shared_covenants INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_covenants INT NOT NULL COMMENT '关联原始契约',
  like_count TINYINT DEFAULT 0 COMMENT '点赞数',
  shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分享时间',
  CONSTRAINT fk_shared_covenants FOREIGN KEY (fk_covenants) REFERENCES t_covenants(pk_covenants) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='共享契约表(社区)';

CREATE TABLE IF NOT EXISTS t_growth_reports (
  pk_growth_reports INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  period VARCHAR(20) NOT NULL COMMENT '时间范围: semester/year/all',
  pdf_url VARCHAR(255) NOT NULL COMMENT 'PDF URL',
  include_peer_comparison TINYINT(1) DEFAULT 1 COMMENT '是否含同龄对比',
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  CONSTRAINT fk_growth_reports_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生成报告表';

CREATE TABLE IF NOT EXISTS t_task_weekly_progress (
  pk_task_weekly_progress INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  week_number TINYINT NOT NULL COMMENT '周数',
  `year` TINYINT NOT NULL COMMENT '年份',
  completed_days TINYINT DEFAULT 0 COMMENT '完成天数',
  total_days TINYINT DEFAULT 7 COMMENT '总天数',
  progress_percent DECIMAL(5,2) DEFAULT 0 COMMENT '完成百分比',
  fk_habit_sops INT COMMENT '关联本周习惯',
  CONSTRAINT fk_weekly_progress_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users),
  CONSTRAINT fk_weekly_progress_habit FOREIGN KEY (fk_habit_sops) REFERENCES t_habit_sops(pk_habit_sops),
  CONSTRAINT uq_weekly_progress UNIQUE (fk_users, `year`, week_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每周打卡进度表';
