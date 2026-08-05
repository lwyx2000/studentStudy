# 小树成长岛 前端 Dockerfile
# 多阶段构建：构建阶段 + 输出阶段（构建产物写入共享 volume，由 nginx 挂载）
# 注意：Vite 8 要求 Node >= 20.19 / >= 22.12，故使用 node:22-alpine (LTS)

# ==================== 构建阶段 ====================
FROM node:22-alpine AS builder

LABEL maintainer="studentstudy-frontend"
LABEL stage="builder"

WORKDIR /app

# 项目无 lockfile，使用 npm install
COPY package.json ./
RUN npm install --no-audit --no-fund

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
