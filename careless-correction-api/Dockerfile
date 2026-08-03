# 小树成长岛 后端 API Dockerfile
# 参考 akshare-docker 后端镜像构建方式，适配 FastAPI + SQLite

FROM python:3.12-slim

LABEL maintainer="studentstudy"
LABEL description="小树成长岛 FastAPI 后端服务"

WORKDIR /app

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# curl 用于健康检查；SQLite 场景无需 gcc/mysql 客户端库
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 数据目录：SQLite 数据库(data/) + 上传文件(uploads/)
RUN mkdir -p /app/data /app/uploads

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=60 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    -r requirements.txt

COPY . .

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:3001/health || exit 1

# 端口与本地开发保持一致(3001)，供 nginx 反向代理
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
