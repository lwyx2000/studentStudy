# 小树成长岛 前端 Dockerfile
# 多阶段构建：构建阶段 + 输出阶段（构建产物写入共享 volume，由 nginx 挂载）
# 注意：Vite 8 基于 rolldown，其原生 binding 在部分 npm 版本下不会随 npm install 自动安装
#       （npm 可选依赖解析 bug #4828），故构建阶段显式补装 linux-x64-musl 平台的 binding。
# Vite 8 要求 Node >= 20.19 / >= 22.12，故使用 node:22-alpine (LTS)

# ==================== 构建阶段 ====================
FROM node:22-alpine AS builder

LABEL maintainer="studentstudy-frontend"
LABEL stage="builder"

WORKDIR /app

# 仅拷贝 package.json（不拷贝 Windows 下生成的 package-lock.json，避免跨平台 lock 干扰依赖解析）
COPY package.json ./

# 升级 npm 到最新，修复可选依赖解析 bug（#4828，会导致 rolldown 原生 binding 漏装）
RUN npm install -g npm@latest || true

# 安装依赖；显式包含可选依赖（rolldown 的 linux-x64-musl 原生 binding）
RUN npm install --no-audit --no-fund --include=optional

# 兜底：若 npm 仍未装上 rolldown 的原生 binding，则按已安装的 rolldown 版本显式补装当前平台对应 binding
# 用 fs 直接读取 node_modules/rolldown/package.json 拿版本，避免 require 受 exports 限制而探测失败
RUN RV=$(node -e "const fs=require('fs');try{const v=JSON.parse(fs.readFileSync('node_modules/rolldown/package.json','utf8')).version;console.log(v)}catch(e){}" 2>/dev/null) && \
    if [ -n "$RV" ] && ! node -e "require('@rolldown/binding-linux-x64-musl')" 2>/dev/null; then \
      echo "rolldown binding 缺失，补装 @rolldown/binding-linux-x64-musl@$RV"; \
      npm install --no-audit --no-fund --no-save "@rolldown/binding-linux-x64-musl@$RV" || \
      npm install --no-audit --no-fund --no-save @rolldown/binding-linux-x64-musl; \
    fi

COPY . .

RUN npm run build

# ==================== 输出阶段 ====================
FROM alpine:3.20

LABEL maintainer="studentstudy-frontend"
LABEL stage="output"

WORKDIR /app

COPY --from=builder /app/dist /app/dist-orig

# 将构建产物拷贝到共享 volume (/app/dist)，供 nginx 的 /var/www/html 挂载
# 先清理旧文件，再复制新产物，避免旧 hash 文件残留导致页面不更新
CMD rm -rf /app/dist/* && cp -rf /app/dist-orig/. /app/dist/
