-- 打卡闭环增强：习惯分值、驳回原因、完成项快照 + 苹果兑换审批流
-- 1) t_check_ins 增加习惯分与驳回原因
ALTER TABLE t_check_ins ADD COLUMN habit_points INTEGER NOT NULL DEFAULT 0;
ALTER TABLE t_check_ins ADD COLUMN reject_reason TEXT NULL;

-- 2) 当日完成任务快照（JSON 数组：[{title, icon, points}]），解决任务每日重置导致详情失真
ALTER TABLE t_check_ins ADD COLUMN completed_tasks_snapshot TEXT NULL;

-- 3) 苹果兑换审批流：孩子申请 → 家长审批 → 扣苹果
CREATE TABLE IF NOT EXISTS t_apple_redemption_requests (
    pk_apple_redemption_requests INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_users INTEGER NOT NULL REFERENCES t_users(pk_users),
    count INTEGER NOT NULL,
    reason VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL,
    approved_at DATETIME NULL
);
