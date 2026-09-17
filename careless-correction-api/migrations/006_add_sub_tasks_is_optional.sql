-- 为子任务表添加可选标记：is_optional=1 表示可选子任务（加分项，不影响家长审核），默认 0（必做）
ALTER TABLE t_sub_tasks
  ADD COLUMN is_optional TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可选子任务: 0=必做, 1=可选(加分项)' AFTER sort_order;
