-- 为用户表新增 apples 字段，持久化苹果数量
ALTER TABLE t_users ADD COLUMN apples INT NOT NULL DEFAULT 0 COMMENT '苹果数量';

-- 新增苹果变动记录表
CREATE TABLE IF NOT EXISTS t_apple_history (
  pk_apple_history INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  fk_users INT NOT NULL COMMENT '关联用户',
  amount INT NOT NULL COMMENT '变动数量(正数=种出,负数=兑换)',
  reason VARCHAR(200) NOT NULL COMMENT '变动原因',
  type VARCHAR(10) NOT NULL COMMENT 'grow=种出苹果, redeem=兑换苹果',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  CONSTRAINT fk_apple_history_user FOREIGN KEY (fk_users) REFERENCES t_users(pk_users) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='苹果变动记录表';
