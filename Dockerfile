# =============================================
# WealthHome Docker 镜像 - 飞牛 OS NAS 部署
# 单容器同时运行 FastAPI 后端 + Vue SPA 前端
# =============================================

FROM python:3.12-slim

LABEL maintainer="xingren"
LABEL description="WealthHome - 家庭资产管理系统"

# 安装系统依赖（akshare 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── 目录结构 ──
# /app/
#   ├── backend/          ← 后端代码 (WORKDIR)
#   │   ├── app/main.py
#   │   ├── requirements.txt
#   │   └── ...
#   ├── frontend/dist/    ← 前端 SPA 构建产物
#   └── data/             ← 数据库等持久化数据 (卷挂载)

WORKDIR /app/backend

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端构建产物
COPY frontend/dist/ /app/frontend/dist/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 创建数据目录（外部卷挂载）
RUN mkdir -p /app/data

# 环境变量
ENV JWT_SECRET=""
ENV DB_PATH="/app/data/wealthhome.db"
ENV TUSHARE_TOKEN=""
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

# 启动服务 (WORKDIR=/app/backend → uvicorn app.main:app)
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
