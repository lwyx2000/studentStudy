# 小树成长岛 (studentStudy) Docker 部署指南

> 本部署方案参考 `akshare-docker` 部署目录改造，适配本项目**单仓库 monorepo** 结构。
> 前、后端在同一个 GitHub 仓库 `git@github.com:lwyx2000/studentStudy.git` 中，服务器上整仓 clone 后由 docker compose 构建部署。

## 1. 架构与文件清单

```
studentStudy/
├── Jenkinsfile                    # Jenkins 部署流水线（核心）
├── docker-compose.yml             # 三容器编排（backend + frontend + nginx）
├── .env.example                   # 部署环境变量模板
├── deploy.sh                      # 手动部署脚本（等效于流水线）
├── docs/deploy.md                 # 本文档
├── nginx/
│   └── nginx.conf                 # 反向代理 + 前端静态资源
├── careless-correction/
│   ├── Dockerfile                 # 前端多阶段构建（node:22-alpine 构建 → alpine 输出）
│   └── .dockerignore
└── careless-correction-api/
    ├── Dockerfile                 # 后端 FastAPI 镜像（python:3.12-slim）
    └── .dockerignore
```

运行架构：

```
                    ┌────────────────────────────────────────┐
 浏览器 ──:8061──▶  │ Nginx (studentstudy-nginx)             │
                    │  ├─ /            → 前端静态文件(volume) │
                    │  ├─ /api/        → 反代 backend:3001   │
                    │  ├─ /uploads/    → 反代 backend:3001   │
                    │  └─ /health      → 健康检查             │
                    └──────────┬─────────────────────────────┘
                               │ docker 网络 studentstudy-network
                    ┌──────────▼─────────────────────────────┐
                    │ Backend (studentstudy-backend:3001)     │
                    │  ├─ SQLite → volume studentstudy-app-data
                    │  └─ 上传文件 → volume studentstudy-app-uploads
                    └─────────────────────────────────────────┘
  构建时: Frontend (node 构建) → dist → volume studentstudy-frontend-dist
```

## 2. 服务器前置要求

| 项目 | 要求 |
|------|------|
| 系统 | Linux（推荐 Ubuntu 22.04+ / Debian 12） |
| Docker | 24+（`docker --version` 验证） |
| Docker Compose | v2（`docker compose version` 验证；兼容 v1 `docker-compose`） |
| Git | `git --version` |
| GitHub 部署密钥 | 服务器 `~/.ssh/` 需配置可访问 `lwyx2000/studentStudy` 的 SSH 密钥（服务器直接 git clone 方式） |
| 端口 | 对外放行 `8061`（可在 `.env` 中修改 `NGINX_PORT`） |

### 2.1 配置 GitHub 部署密钥（服务器）

```bash
# 在服务器上
ssh-keygen -t ed25519 -C "deploy@studentstudy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
# 将公钥添加到 GitHub: 仓库 Settings → Deploy keys → Add deploy key
#   标题: studentstudy-deploy，勾选 Allow write access（如需写权限）

# 让 ssh 识别非默认文件名的密钥（写入 ~/.ssh/config）
cat >> ~/.ssh/config <<'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_deploy
    StrictHostKeyChecking no
EOF
chmod 600 ~/.ssh/config

# 验证连通性
git ls-remote git@github.com:lwyx2000/studentStudy.git HEAD
```

首次连接自动信任主机指纹（流水线/脚本已内置 `ssh-keyscan github.com`）。

## 3. 方式一：Jenkins 流水线部署（推荐）

### 3.1 Jenkins 侧准备

1. **安装插件**：`Pipeline`、`SSH Agent`（如用凭据绑定的私钥）；如服务器直连 GitHub 走 deploy key，无需其他插件。
2. **创建凭据**：`系统管理 → 凭据 → 全局 → 添加凭据`，类型选择 **SSH Username with private key**：
   - ID（username）: `sos`
   - Private key：粘贴**能免密登录部署服务器**的私钥（对应 `sos@192.168.3.53`）
   - ID（credentialsId）: `sos`（与 Jenkinsfile 中 `SSH_CREDENTIALS_ID` 一致）

3. **新建流水线任务**：
   - `新建任务 → 流水线(Pipeline)`
   - **Pipeline** 章节 → **Definition**: `Pipeline script from SCM`
     - SCM: `Git`，仓库地址 `git@github.com:lwyx2000/studentStudy.git`
     - 凭据：Jenkins 访问 GitHub 的凭据（若 Jenkins 已能访问 GitHub 可省略）
     - Script Path: `Jenkinsfile`
   - 或选择 **Definition: Pipeline script** 直接粘贴 `Jenkinsfile` 内容

### 3.2 构建参数说明

首次点击 **Build with Parameters**，参数如下：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| GIT_BRANCH | `main` | 部署的分支 |
| DEPLOY_SERVER | 空（用环境变量 `sos@192.168.3.53`） | 覆盖部署服务器 |
| DEPLOY_PATH | 空（用环境变量 `/home/sos/apps/studentstudy`） | 覆盖服务器部署目录 |
| SKIP_TESTS | false | 跳过健康检查 |
| FORCE_REBUILD | false | `--no-cache` 全量重建镜像 |
| FORCE_PULL | true | 清空 `src/` 重新 clone；false 时增量 `git pull` |
| DEPLOY_TARGET | `all` | `all` / `backend` / `frontend` 局部部署 |
| DEPLOY_ACTION | `deploy` | `deploy` / `build-only` / `stop` / `restart` |

### 3.3 流水线阶段

| 阶段 | 作用 |
|------|------|
| 环境检查 | 校验服务器 Docker/Compose、GitHub 连通性，探测 compose 命令 |
| 验证基础镜像 | 检查 `python:3.12-slim` / `node:22-alpine` / `alpine:3.20` / `nginx:alpine` 是否已拉取（缺失会提示手动 `docker pull`） |
| 宿主机拉取代码 | clone/更新仓库到 `$DEPLOY_PATH/src`，同步 compose/nginx/.env 配置 |
| 构建 Docker 镜像 | `docker compose build` |
| 启动服务 | 清理前端 volume 后 `up -d --force-recreate` |
| 健康检查 | Nginx `/health` + 后端容器健康状态 + API 经 Nginx 连通性（401/200） |
| 停止 / 重启 | `DEPLOY_ACTION=stop / restart` 时执行 |

### 3.4 首次部署后验证

```bash
# 浏览器访问
http://192.168.3.53:8061            # 前端
http://192.168.3.53:8061/docs       # 后端 API 文档（Swagger，nginx 已反代 /docs）
http://192.168.3.53:8061/redoc      # ReDoc 文档

# 服务器上检查
docker compose -p studentstudy ps
curl -sf http://localhost:8061/health
```

## 4. 方式二：手动脚本部署

不需要 Jenkins 时，在项目根目录直接执行（需要本机可 ssh 到服务器）：

```bash
bash deploy.sh                                        # 默认 sos@192.168.3.53
DEPLOY_SERVER=root@1.2.3.4 DEPLOY_PATH=/opt/studentStudy bash deploy.sh
```

脚本逻辑与流水线一致：环境检查 → 拉代码 → 同步配置 → 构建启动 → 健康检查。

## 5. 数据持久化与备份

| Volume | 内容 | 说明 |
|--------|------|------|
| `studentstudy-app-data` | SQLite 数据库（`/app/data/app.db`） | **核心数据，务必备份** |
| `studentstudy-app-uploads` | 上传图片（错题/打卡照片） | 建议定期备份 |
| `studentstudy-frontend-dist` | 前端构建产物 | 重建时会清理，无需备份 |

备份命令（服务器上执行）：

```bash
# 数据库
docker run --rm -v studentstudy-app-data:/data -v $(pwd):/backup alpine tar czf /backup/app-data-$(date +%F).tar.gz -C /data .
# 上传文件
docker run --rm -v studentstudy-app-uploads:/data -v $(pwd):/backup alpine tar czf /backup/app-uploads-$(date +%F).tar.gz -C /data .
```

> 数据库与上传文件全部在 Docker volume 中，**升级镜像 / 重建容器不会丢失数据**。

## 6. 常见问题（FAQ）

**Q1: 报错「无法连接 GitHub」**
服务器未配置 deploy key，或未信任主机指纹。按 [2.1](#21-配置-github-部署密钥服务器) 配置后重试。

**Q2: 报错「基础镜像不存在」**
服务器首次部署需手动拉取基础镜像：

```bash
docker pull python:3.12-slim
docker pull node:22-alpine
docker pull alpine:3.20
docker pull nginx:alpine
```

**Q3: 修改对外端口**
编辑服务器 `$DEPLOY_PATH/.env` 中 `NGINX_PORT` 后重新部署或 `restart` 即可。流水线/脚本只在变量缺失时追加，**不会覆盖**你已有的设置，因此服务器上的自定义端口会被保留。

> 新服务器首次部署时，端口默认取 `Jenkinsfile` 的 `environment`（`NGINX_PORT=8061`）写入 `.env`。

**Q4: 修改 JWT 密钥**
服务器 `$DEPLOY_PATH/.env` 中设置 `JWT_SECRET` 为随机长字符串后 `restart`。注意：**流水线不会覆盖已存在的 `JWT_SECRET`**。

**Q5: 后端端口为什么只监听 127.0.0.1？**
`docker-compose.yml` 中后端映射为 `127.0.0.1:3001:3001`，仅本机可访问，对外统一走 Nginx，避免 API 绕过前端安全策略直接暴露。

**Q6: 如何只更新前端/后端？**
`DEPLOY_TARGET=frontend` 或 `backend`，构建与启动只处理对应服务，减少停机时间。

**Q7: 数据如何迁移到新服务器？**
在新服务器部署成功后，用第 5 节备份的 tar 包恢复 `app-data` 与 `app-uploads` 两个 volume 即可。

## 7. 升级 / 回滚

- **升级**：修改代码 push 到 `main` → Jenkins 重新执行流水线（或 `bash deploy.sh`）。
- **回滚**：指定旧分支/旧 commit 再执行一次部署；数据库 volume 不清理即可保留数据。
