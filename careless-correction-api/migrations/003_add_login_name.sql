ALTER TABLE t_users
  ADD COLUMN login_name VARCHAR(50) NULL COMMENT '登录名(孩子拼音首字母)' AFTER name,
  ADD UNIQUE INDEX uq_users_login_name (login_name);
