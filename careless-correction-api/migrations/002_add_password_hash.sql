-- 迁移 002：为家长账号添加密码字段
-- 执行前请确保已运行 001_init_mysql.sql

ALTER TABLE t_users
  ADD COLUMN password_hash VARCHAR(255) NULL COMMENT '密码哈希(仅家长)' AFTER role;
