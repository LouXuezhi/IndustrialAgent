#!/bin/bash
# 备份恢复脚本

set -e

BACKUP_DIR="/opt/backups"
COMPOSE_FILE="/opt/industrial-qa/docker-compose.prod.yml"
ENV_FILE="/opt/industrial-qa/.env"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error_exit() {
    echo -e "${RED}❌ 错误: $1${NC}"
    exit 1
}

if [ $# -eq 0 ]; then
    echo -e "${YELLOW}用法: $0 <备份日期时间戳>${NC}"
    echo "示例: $0 20241215_020000"
    echo ""
    echo -e "${GREEN}可用的备份:${NC}"
    if [ -d "$BACKUP_DIR" ]; then
        ls -1d "$BACKUP_DIR"/20* 2>/dev/null | sort -r | head -10 || echo "没有找到备份"
    else
        echo "备份目录不存在: $BACKUP_DIR"
    fi
    exit 1
fi

BACKUP_DATE="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_DATE"

if [ ! -d "$BACKUP_PATH" ]; then
    error_exit "备份目录不存在: $BACKUP_PATH"
fi

echo -e "${RED}⚠️  警告: 这将恢复备份 $BACKUP_DATE${NC}"
echo -e "${RED}⚠️  当前数据将被覆盖！${NC}"
read -p "确认继续? (输入 'yes' 继续): " confirm

if [ "$confirm" != "yes" ]; then
    echo "取消恢复"
    exit 0
fi

# 检查环境变量文件
if [ ! -f "$ENV_FILE" ]; then
    error_exit "环境变量文件不存在: $ENV_FILE"
fi

# 加载环境变量
source "$ENV_FILE"

# 检查 Docker Compose 文件
if [ ! -f "$COMPOSE_FILE" ]; then
    error_exit "Docker Compose 文件不存在: $COMPOSE_FILE"
fi

log "开始恢复备份..."

# 恢复 MySQL
MYSQL_BACKUP=$(ls "$BACKUP_PATH"/mysql_*.sql.gz 2>/dev/null | head -1)
if [ -n "$MYSQL_BACKUP" ]; then
    log "📦 恢复 MySQL 数据库..."
    if gunzip -c "$MYSQL_BACKUP" | \
        docker compose -f "$COMPOSE_FILE" exec -T mysql mysql \
        -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}"; then
        log "✅ MySQL 恢复完成"
    else
        error_exit "MySQL 恢复失败"
    fi
else
    log "⚠️  未找到 MySQL 备份文件"
fi

# 恢复上传文件
UPLOADS_BACKUP=$(ls "$BACKUP_PATH"/uploads_*.tar.gz 2>/dev/null | head -1)
if [ -n "$UPLOADS_BACKUP" ]; then
    log "📦 恢复上传文件..."
    if tar -xzf "$UPLOADS_BACKUP" -C /opt/industrial-qa; then
        log "✅ 上传文件恢复完成"
    else
        error_exit "上传文件恢复失败"
    fi
else
    log "⚠️  未找到上传文件备份"
fi

# 恢复向量数据库
CHROMA_BACKUP=$(ls "$BACKUP_PATH"/chroma_*.tar.gz 2>/dev/null | head -1)
if [ -n "$CHROMA_BACKUP" ]; then
    log "📦 恢复向量数据库..."
    if tar -xzf "$CHROMA_BACKUP" -C /opt/industrial-qa; then
        log "✅ 向量数据库恢复完成"
    else
        error_exit "向量数据库恢复失败"
    fi
else
    log "⚠️  未找到向量数据库备份"
fi

# 恢复 Redis（可选）
REDIS_BACKUP=$(ls "$BACKUP_PATH"/redis_*.rdb 2>/dev/null | head -1)
if [ -n "$REDIS_BACKUP" ]; then
    log "📦 恢复 Redis 数据..."
    if docker cp "$REDIS_BACKUP" industrial-qa-redis-prod:/data/dump.rdb 2>/dev/null; then
        log "✅ Redis 恢复完成（需要重启 Redis 容器生效）"
        log "💡 提示: 运行 'docker compose -f $COMPOSE_FILE restart redis' 重启 Redis"
    else
        log "⚠️  Redis 恢复失败（可能需要手动操作）"
    fi
else
    log "⚠️  未找到 Redis 备份文件"
fi

echo -e "${GREEN}=========================================="
echo "✅ 恢复完成"
echo "==========================================${NC}"
echo ""
echo "建议操作:"
echo "1. 重启应用服务: docker compose -f $COMPOSE_FILE restart app"
echo "2. 验证数据: 检查应用是否正常运行"
echo "3. 测试功能: 登录并测试主要功能"

exit 0

