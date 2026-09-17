-- 打卡记录增加阳光值构成明细：用于家长审批页展示「必做小任务分 / 可选⭐加分 / 全部完成奖励」
ALTER TABLE t_check_ins
  ADD COLUMN required_points INT NOT NULL DEFAULT 0 COMMENT '必做小任务分值合计' AFTER task_count,
  ADD COLUMN optional_bonus INT NOT NULL DEFAULT 0 COMMENT '可选⭐子任务加分合计' AFTER required_points,
  ADD COLUMN all_done_bonus INT NOT NULL DEFAULT 0 COMMENT '全部完成额外奖励' AFTER optional_bonus;
