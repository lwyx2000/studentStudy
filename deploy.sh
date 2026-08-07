#!/usr/bin/env bash
# ============================================================
# 小树成长岛 (studentStudy) 手动部署脚本
# 效果等同于 Jenkins 流水线（服务器 git clone + docker compose 部署）
#
# 用法:
#   bash deploy.sh                                  # 使用默认服务器/目录
#   DEPLOY_SERVER=root@1.2.3.4 DEPLOY_PATH=/opt/studentStudy bash deploy.sh
#
# 前置要求: 服务器已安装 Docker 与 Docker Compose v2，且配置了 GitHub 部署密钥
# ============================================================
set -euo pipefail

# ===== 可配置项 =====
DEPLOY_SERVER="${DEPLOY_SERVER:-sos@192.168.3.53}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/sos/apps/studentstudy}"
GIT_REPO="git@github.com:lwyx2000/studentStudy.git"
GIT_BRANCH="${GIT_BRANCH:-main}"
NGINX_PORT="${NGINX_PORT:-8061}"
COMPOSE_PROJECT="studentstudy"

echo "========================================"
echo "studentStudy 手动部署"
echo "目标: $DEPLOY_SERVER:$DEPLOY_PATH"
echo "分支: $GIT_BRANCH  端口: $NGINX_PORT"
echo "========================================"

DEPLOY_HOST="${DEPLOY_SERVER##*@}"

# 通过环境变量注入参数，远程脚本(heredoc)保持完全字面量，避免转义问题
ssh "$DEPLOY_SERVER" \
  "DEPLOY_PATH='$DEPLOY_PATH' GIT_REPO='$GIT_REPO' GIT_BRANCH='$GIT_BRANCH' \
   NGINX_PORT='$NGINX_PORT' COMPOSE_PROJECT='$COMPOSE_PROJECT' DEPLOY_HOST='$DEPLOY_HOST' bash -s" <<'REMOTE'
set -e
export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no"

echo ""
echo ">>> [1/5] 环境检查"
docker --version
(docker compose version || docker-compose version) 2>&1 | head -1
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
git ls-remote "$GIT_REPO" HEAD >/dev/null 2>&1 \
  && echo "GitHub 连通 OK" \
  || echo "警告: 无法连接 GitHub（请检查服务器 ~/.ssh 部署密钥）"

echo ""
echo ">>> [2/5] 拉取代码"
mkdir -p "$DEPLOY_PATH/nginx"
if [ ! -d "$DEPLOY_PATH/src/.git" ]; then
  git clone --depth 1 -b "$GIT_BRANCH" "$GIT_REPO" "$DEPLOY_PATH/src"
  echo "已 clone 仓库到 $DEPLOY_PATH/src"
else
  git -C "$DEPLOY_PATH/src" fetch origin
  git -C "$DEPLOY_PATH/src" reset --hard "origin/$GIT_BRANCH"
  echo "已更新仓库到 origin/$GIT_BRANCH"
fi
# 验证代码版本
echo "--- 验证代码版本 ---"
git -C "$DEPLOY_PATH/src" log --oneline -1
REMOTE_HASH=$(git ls-remote "$GIT_REPO" "refs/heads/$GIT_BRANCH" | cut -c1-7)
LOCAL_HASH=$(git -C "$DEPLOY_PATH/src" log --oneline -1 | cut -d' ' -f1)
echo "远程最新: $REMOTE_HASH  本地: $LOCAL_HASH"
if [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
  echo "错误: 本地代码与远程不一致，拉取失败！"
  exit 1
fi

echo ""
echo ">>> [3/5] 同步部署配置"
cp -f "$DEPLOY_PATH/src/docker-compose.yml" "$DEPLOY_PATH/docker-compose.yml"
cp -f "$DEPLOY_PATH/src/nginx/nginx.conf" "$DEPLOY_PATH/nginx/nginx.conf"
cp -f "$DEPLOY_PATH/src/.env.example" "$DEPLOY_PATH/.env.example"
if [ ! -f "$DEPLOY_PATH/.env" ]; then
  cp "$DEPLOY_PATH/.env.example" "$DEPLOY_PATH/.env"
  echo "已从 .env.example 创建 .env 文件"
fi
# 初始化非敏感配置：仅当缺失时从 .env.example 追加（不覆盖已存在的值，保留服务器自定义）
for var in SRC_DIR NGINX_PORT BACKEND_PORT; do
  new_val=$(grep "^${var}=" "$DEPLOY_PATH/.env.example" 2>/dev/null | cut -d= -f2-)
  if [ -n "$new_val" ] && ! grep -q "^${var}=" "$DEPLOY_PATH/.env" 2>/dev/null; then
    echo "${var}=${new_val}" >> "$DEPLOY_PATH/.env"
    echo "已添加 .env: ${var}=${new_val}"
  fi
done

echo ""
echo ">>> [4/5] 构建并启动"
cd "$DEPLOY_PATH"
COMPOSE_CMD="docker compose"
docker compose version >/dev/null 2>&1 || COMPOSE_CMD="docker-compose"
echo "Compose 命令: $COMPOSE_CMD"
$COMPOSE_CMD -p "$COMPOSE_PROJECT" build
# 清理前端构建产物 volume，避免旧文件残留（数据 volume 不受影响）
docker volume rm studentstudy-frontend-dist 2>/dev/null && echo "前端 volume 已清理" || echo "前端 volume 清理跳过"
$COMPOSE_CMD -p "$COMPOSE_PROJECT" up -d --force-recreate
sleep 10
$COMPOSE_CMD -p "$COMPOSE_PROJECT" ps

echo ""
echo ">>> [5/5] 健康检查"
for i in $(seq 1 30); do
  if curl -sf "http://localhost:$NGINX_PORT/health" > /dev/null 2>&1; then
    echo "Nginx 健康检查通过"
    break
  fi
  echo "等待 Nginx 就绪... ($i/30)"
  sleep 2
  [ "$i" -eq 30 ] && echo "Nginx 健康检查超时" && exit 1
done
for i in $(seq 1 30); do
  status=$(docker inspect --format "{{.State.Health.Status}}" studentstudy-backend 2>/dev/null)
  echo "后端状态: $status ($i/30)"
  if [ "$status" = "healthy" ]; then
    echo "后端健康检查通过"
    break
  fi
  if [ "$status" = "unhealthy" ]; then
    echo "后端健康检查失败"
    exit 1
  fi
  sleep 2
  [ "$i" -eq 30 ] && echo "后端健康检查超时" && exit 1
done
code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$NGINX_PORT/api/v1/auth/session")
echo "API 返回码: $code"
if [ "$code" = "401" ] || [ "$code" = "200" ]; then
  echo "API 连通性验证通过"
else
  echo "API 连通性验证失败 (HTTP $code)"
  exit 1
fi

echo ""
echo "========================================"
echo "部署成功! 访问地址: http://$DEPLOY_HOST:$NGINX_PORT"
echo "========================================"
REMOTE
