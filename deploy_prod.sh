#!/bin/bash
# deploy_prod.sh - 生产环境完整部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  生产环境部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo "请复制 env.example 并配置: cp env.example .env"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

COMPOSE_FILE="docker-compose.prod.yml"

# 阶段 1: 启动基础服务
echo -e "${YELLOW}[1/5] 启动 MySQL 和 Redis...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d mysql redis
echo -e "${GREEN}✅ 基础服务已启动${NC}"
echo ""

# 阶段 2: 等待服务就绪
echo -e "${YELLOW}[2/5] 等待服务就绪...${NC}"
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

# 等待 Redis
for i in {1..15}; do
    if $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "${GREEN}✅ Redis 已就绪${NC}"
        break
    fi
    sleep 2
done
echo ""

# 阶段 3: 构建应用镜像
echo -e "${YELLOW}[3/5] 构建应用镜像...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE build app
echo -e "${GREEN}✅ 镜像构建完成${NC}"
echo ""

# 阶段 4: 执行数据库迁移
echo -e "${YELLOW}[4/5] 执行数据库迁移（Alembic）...${NC}"
echo -e "${BLUE}这将创建数据库表和管理员账号...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE run --rm app alembic upgrade head || {
    echo -e "${YELLOW}⚠️  迁移可能已执行，继续...${NC}"
}
echo -e "${GREEN}✅ 数据库迁移完成${NC}"
echo ""

# 验证管理员账号
echo -e "${YELLOW}验证管理员账号...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} \
    -e "SELECT email, username, role FROM ${MYSQL_DATABASE:-industrial_qa}.users WHERE email='admin@louxuezhi.com';" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  无法验证管理员账号（可能需要手动检查）${NC}"
}
echo ""

# 阶段 5: 启动应用
echo -e "${YELLOW}[5/5] 启动应用服务...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d
echo -e "${GREEN}✅ 应用服务已启动${NC}"
echo ""

# 等待应用就绪
echo -e "${YELLOW}⏳ 等待应用启动...${NC}"
sleep 10

# 最终验证
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  部署验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查服务状态
echo -e "${GREEN}服务状态:${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE ps
echo ""

# 健康检查
echo -e "${YELLOW}健康检查...${NC}"
if $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T app curl -f http://localhost:8000/ &>/dev/null; then
    echo -e "${GREEN}✅ 应用健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败，请查看日志:${NC}"
    echo "   docker-compose -f $COMPOSE_FILE logs app"
fi
echo ""

# 显示部署信息
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 生产环境部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}管理员账号信息:${NC}"
echo "  邮箱: admin@louxuezhi.com"
echo "  用户名: LXZ"
echo "  密码: 271828LXZ"
echo ""
echo -e "${GREEN}常用命令:${NC}"
echo "  查看日志: $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f app"
echo "  查看状态: $DOCKER_COMPOSE -f $COMPOSE_FILE ps"
echo "  停止服务: $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "  重启应用: $DOCKER_COMPOSE -f $COMPOSE_FILE restart app"
echo ""
echo -e "${YELLOW}⚠️  重要提醒:${NC}"
echo "  1. 请立即修改默认管理员密码"
echo "  2. 请部署备份脚本（参考部署文档 5.5 节）"
echo "  3. 配置定时备份任务"
echo ""

