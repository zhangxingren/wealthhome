#!/usr/bin/env bash
# =============================================
# WealthHome NAS 部署脚本 (飞牛 OS / Docker)
# =============================================
# 用法:
#   chmod +x deploy.sh
#   ./deploy.sh              # 构建并启动（全新数据库）
#   ./deploy.sh --with-data  # 构建并启动（附带测试数据）
# =============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════╗"
echo "║   WealthHome NAS Docker 部署工具     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 检查 Docker ──
if ! command -v docker &>/dev/null; then
    echo "❌ 未安装 Docker，请先在飞牛 OS 应用中心安装 Docker"
    exit 1
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
    echo "❌ 未找到 docker-compose，请安装 Docker Compose"
    exit 1
fi

COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker compose"
fi

# ── 构建前端 ──
echo "📦 步骤 1/4: 构建前端..."
if [ -d "frontend/node_modules" ] && [ -f "frontend/node_modules/.bin/vite" ]; then
    cd frontend && npx vite build && cd ..
else
    echo "⚠️  前端依赖未安装，跳过前端构建（使用已有 dist）"
    if [ ! -f "frontend/dist/index.html" ]; then
        echo "❌ 前端构建产物不存在！请先在开发机执行: cd frontend && npm install && npm run build"
        exit 1
    fi
fi

# ── 处理数据 ──
if [ "${1:-}" = "--with-data" ]; then
    echo "📊 步骤 2/4: 复制测试数据..."
    if [ -f "backend/wealthhome.db" ]; then
        mkdir -p docker-data
        cp backend/wealthhome.db docker-data/wealthhome.db
        echo "   已复制 wealthhome.db → docker-data/"
    fi
fi

# ── 构建镜像 ──
echo "🐳 步骤 3/4: 构建 Docker 镜像..."
docker build -t wealthhome:latest .

# ── 停止旧容器 ──
echo "🧹 停止旧容器..."
$COMPOSE_CMD down 2>/dev/null || true

# ── 启动 ──
echo "🚀 步骤 4/4: 启动服务..."
$COMPOSE_CMD up -d

sleep 3

# ── 验证 ──
echo ""
if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "✅ WealthHome 已启动！"
    echo "   地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):8000"
    echo ""
    echo "📝 常用命令:"
    echo "   查看日志:    $COMPOSE_CMD logs -f"
    echo "   停止服务:    $COMPOSE_CMD down"
    echo "   重启服务:    $COMPOSE_CMD restart"
    echo "   查看状态:    $COMPOSE_CMD ps"
else
    echo "⚠️  服务已启动但健康检查失败，查看日志: $COMPOSE_CMD logs"
fi
