#!/bin/bash
# deploy.sh - Docker 部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
ENV=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "${YELLOW}⚠️  使用生产环境配置${NC}"
else
    echo -e "${GREEN}📦 使用开发环境配置${NC}"
fi

echo ""
echo "🚀 开始部署 Industrial QA Backend..."
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo "请复制 env.example 并配置: cp env.example .env"
    exit 1
fi

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

# 使用 docker compose（新版本）或 docker-compose（旧版本）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 构建镜像
echo -e "${GREEN}📦 构建 Docker 镜像...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE build

# 启动服务
echo -e "${GREEN}🚀 启动服务...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d

# 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 15

# 检查服务状态
echo -e "${GREEN}✅ 检查服务状态...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE ps

# 等待 MySQL 就绪
echo -e "${YELLOW}⏳ 等待 MySQL 就绪...${NC}"
for i in {1..30}; do
    if $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo -e "${GREEN}✅ MySQL 已就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ MySQL 启动超时${NC}"
        exit 1
    fi
    sleep 2
done

# 初始化数据库
echo -e "${GREEN}🗄️  初始化数据库...${NC}"
if [ "$ENV" = "prod" ]; then
    # 生产环境使用 Alembic 迁移
    echo -e "${YELLOW}使用 Alembic 迁移数据库（生产环境）...${NC}"
    $DOCKER_COMPOSE -f $COMPOSE_FILE run --rm app alembic upgrade head || {
        echo -e "${YELLOW}⚠️  迁移可能已执行，跳过...${NC}"
    }
else
    # 开发环境使用 init_db.py
    echo -e "${YELLOW}使用 init_db.py 初始化数据库（开发环境）...${NC}"
    $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T app python scripts/init_db.py || {
        echo -e "${YELLOW}⚠️  数据库初始化可能已存在，跳过...${NC}"
    }
fi

# 最终检查
echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "📍 API 文档: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/"
echo ""
echo "常用命令:"
echo "  查看日志: $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f app"
echo "  停止服务: $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "  重启服务: $DOCKER_COMPOSE -f $COMPOSE_FILE restart app"
echo ""

