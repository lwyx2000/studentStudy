CREATE TABLE IF NOT EXISTS t_sub_tasks (
  pk_sub_tasks INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_tasks INT NOT NULL COMMENT '关联任务',
  title VARCHAR(100) NOT NULL COMMENT '子任务标题',
  type VARCHAR(20) NOT NULL COMMENT '子任务类别: morning_routine/study_habit/life_skill/exercise/reflection',
  week_day VARCHAR(10) COMMENT '适用日: weekday=平时, weekend=周末, NULL=全部',
  sort_order TINYINT DEFAULT 0 COMMENT '排序序号',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_sub_tasks_task FOREIGN KEY (fk_tasks) REFERENCES t_tasks(pk_tasks) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='子任务表';
