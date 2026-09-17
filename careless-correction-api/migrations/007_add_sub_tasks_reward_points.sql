-- 为子任务表添加独立阳光值：每个小任务完成可获得自己的分值
-- reward_points 为 NULL 表示默认：必做子任务继承主任务分值，可选 ⭐ 子任务默认 +2
ALTER TABLE t_sub_tasks
  ADD COLUMN reward_points SMALLINT NULL COMMENT '子任务独立阳光值: NULL=默认(必做继承主任务分值, 可选⭐默认+2)' AFTER is_optional;
