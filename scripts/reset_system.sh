#!/bin/bash
# reset_system.sh - 重置系统脚本（删除所有数据并重新初始化）

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}  ⚠️  系统重置警告${NC}"
echo -e "${RED}========================================${NC}"
echo ""
echo -e "${YELLOW}此操作将：${NC}"
echo "  1. 停止所有服务"
echo "  2. 删除 MySQL 数据库中的所有数据"
echo "  3. 清空 Redis 缓存"
echo "  4. 删除向量数据库（ChromaDB）"
echo "  5. 删除所有上传的文件"
echo "  6. 重新初始化数据库"
echo ""
echo -e "${RED}⚠️  此操作不可恢复！所有数据将被永久删除！${NC}"
echo ""

# 确认操作
read -p "确认要重置系统吗？请输入 'YES' 继续: " confirm
if [ "$confirm" != "YES" ]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  开始重置系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检测环境
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    ENV="prod"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
    ENV="dev"
else
    echo -e "${RED}❌ 未找到 docker-compose 文件${NC}"
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

# 步骤 1: 停止服务
echo -e "${YELLOW}[1/6] 停止所有服务...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE down
echo -e "${GREEN}✅ 服务已停止${NC}"
echo ""

# 步骤 2: 删除数据库数据
echo -e "${YELLOW}[2/6] 删除数据库数据...${NC}"

# 使用 docker compose down -v 删除数据卷（更可靠）
echo -e "${BLUE}删除所有数据卷...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE down -v 2>/dev/null || {
    echo -e "${YELLOW}⚠️  部分数据卷可能不存在，继续...${NC}"
}

# 额外清理：查找并删除可能遗留的数据卷
echo -e "${BLUE}清理遗留数据卷...${NC}"
if [ "$ENV" = "prod" ]; then
    # 生产环境数据卷
    docker volume ls | grep -E "(mysql_data_prod|redis_data_prod)" | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true
else
    # 开发环境数据卷
    docker volume ls | grep -E "(mysql_data|redis_data)" | grep -v "_prod" | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true
fi

echo -e "${GREEN}✅ 数据库数据已删除${NC}"
echo ""

# 步骤 3: 删除向量数据库
echo -e "${YELLOW}[3/6] 删除向量数据库（ChromaDB）...${NC}"
if [ -d "chroma_store" ]; then
    rm -rf chroma_store/*
    echo -e "${GREEN}✅ 向量数据库已清空${NC}"
else
    echo -e "${YELLOW}⚠️  chroma_store 目录不存在，跳过...${NC}"
fi
echo ""

# 步骤 4: 删除上传的文件
echo -e "${YELLOW}[4/6] 删除上传的文件...${NC}"
if [ -d "data/uploads" ]; then
    rm -rf data/uploads/*
    echo -e "${GREEN}✅ 上传文件已删除${NC}"
else
    echo -e "${YELLOW}⚠️  data/uploads 目录不存在，跳过...${NC}"
fi
echo ""

# 步骤 5: 重新启动服务
echo -e "${YELLOW}[5/6] 重新启动服务...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d mysql redis
echo -e "${GREEN}✅ 基础服务已启动${NC}"

# 等待 MySQL 就绪
echo -e "${BLUE}等待 MySQL 就绪...${NC}"
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

# 等待 Redis 就绪
echo -e "${BLUE}等待 Redis 就绪...${NC}"
for i in {1..15}; do
    if $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "${GREEN}✅ Redis 已就绪${NC}"
        break
    fi
    sleep 2
done
echo ""

# 步骤 6: 重新初始化数据库
echo -e "${YELLOW}[6/6] 重新初始化数据库...${NC}"
if [ "$ENV" = "prod" ]; then
    # 生产环境：使用 Alembic 迁移
    echo -e "${BLUE}执行 Alembic 迁移...${NC}"
    $DOCKER_COMPOSE -f $COMPOSE_FILE build app
    $DOCKER_COMPOSE -f $COMPOSE_FILE run --rm app alembic upgrade head
    echo -e "${GREEN}✅ 数据库迁移完成${NC}"
    
    # 验证管理员账号
    echo -e "${BLUE}验证管理员账号...${NC}"
    $DOCKER_COMPOSE -f $COMPOSE_FILE exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} \
        -e "SELECT email, username, role FROM ${MYSQL_DATABASE:-industrial_qa}.users WHERE email='admin@louxuezhi.com';" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  无法验证管理员账号${NC}"
    }
else
    # 开发环境：使用 init_db.py
    echo -e "${BLUE}使用 init_db.py 初始化数据库...${NC}"
    $DOCKER_COMPOSE -f $COMPOSE_FILE build app
    $DOCKER_COMPOSE -f $COMPOSE_FILE run --rm app python scripts/init_db.py
    echo -e "${GREEN}✅ 数据库初始化完成${NC}"
fi
echo ""

# 启动应用
echo -e "${YELLOW}启动应用服务...${NC}"
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d
echo -e "${GREEN}✅ 应用服务已启动${NC}"
echo ""

# 等待应用就绪
echo -e "${BLUE}等待应用启动...${NC}"
sleep 10

# 最终验证
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 系统重置完成！${NC}"
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
    echo "   $DOCKER_COMPOSE -f $COMPOSE_FILE logs app"
fi
echo ""

# 显示信息
if [ "$ENV" = "prod" ]; then
    echo -e "${GREEN}管理员账号信息:${NC}"
    echo "  邮箱: admin@louxuezhi.com"
    echo "  用户名: LXZ"
    echo "  密码: 271828LXZ"
    echo ""
fi

echo -e "${GREEN}常用命令:${NC}"
echo "  查看日志: $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f app"
echo "  查看状态: $DOCKER_COMPOSE -f $COMPOSE_FILE ps"
echo "  停止服务: $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo ""

