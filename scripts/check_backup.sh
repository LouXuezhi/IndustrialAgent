#!/bin/bash
# 检查备份状态脚本

BACKUP_DIR="/opt/backups"
LOG_FILE="/opt/backups/backup_check.log"
MAX_AGE_HOURS=25  # 如果超过 25 小时没有备份，报警

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查备份目录
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ 备份目录不存在: $BACKUP_DIR${NC}"
    exit 1
fi

# 检查最近的备份
LATEST_BACKUP=$(ls -td "$BACKUP_DIR"/20* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}❌ 没有找到任何备份${NC}"
    log "错误: 没有找到任何备份"
    exit 1
fi

# 获取备份时间
if [ -f "$LATEST_BACKUP" ]; then
    BACKUP_TIME=$(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || stat -f %m "$LATEST_BACKUP" 2>/dev/null)
else
    BACKUP_TIME=$(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || stat -f %m "$LATEST_BACKUP" 2>/dev/null)
fi

CURRENT_TIME=$(date +%s)
AGE_HOURS=$(( (CURRENT_TIME - BACKUP_TIME) / 3600 ))

# 检查备份文件完整性
BACKUP_NAME=$(basename "$LATEST_BACKUP")
MYSQL_BACKUP=$(find "$LATEST_BACKUP" -name "mysql_*.sql.gz" 2>/dev/null | head -1)
UPLOADS_BACKUP=$(find "$LATEST_BACKUP" -name "uploads_*.tar.gz" 2>/dev/null | head -1)
CHROMA_BACKUP=$(find "$LATEST_BACKUP" -name "chroma_*.tar.gz" 2>/dev/null | head -1)

# 验证备份文件
BACKUP_VALID=true
if [ -z "$MYSQL_BACKUP" ]; then
    echo -e "${YELLOW}⚠️  警告: 未找到 MySQL 备份${NC}"
    BACKUP_VALID=false
elif [ ! -s "$MYSQL_BACKUP" ]; then
    echo -e "${RED}❌ 错误: MySQL 备份文件为空${NC}"
    BACKUP_VALID=false
fi

# 显示备份信息
echo -e "${BLUE}=========================================="
echo "备份状态检查"
echo "==========================================${NC}"
echo ""
echo -e "最新备份: ${GREEN}$BACKUP_NAME${NC}"
echo -e "备份时间: $(date -d @$BACKUP_TIME '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r $BACKUP_TIME '+%Y-%m-%d %H:%M:%S' 2>/dev/null)"
echo -e "备份年龄: ${AGE_HOURS} 小时"

if [ $AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo -e "${RED}⚠️  警告: 备份已超过 ${MAX_AGE_HOURS} 小时！${NC}"
    log "警告: 备份已超过 ${MAX_AGE_HOURS} 小时"
    BACKUP_VALID=false
else
    echo -e "${GREEN}✅ 备份时间正常${NC}"
fi

echo ""
echo -e "${BLUE}备份文件检查:${NC}"
if [ -n "$MYSQL_BACKUP" ]; then
    SIZE=$(du -h "$MYSQL_BACKUP" | cut -f1)
    echo -e "  MySQL: ${GREEN}✅${NC} ($SIZE)"
else
    echo -e "  MySQL: ${RED}❌${NC} (未找到)"
fi

if [ -n "$UPLOADS_BACKUP" ]; then
    SIZE=$(du -h "$UPLOADS_BACKUP" | cut -f1)
    echo -e "  上传文件: ${GREEN}✅${NC} ($SIZE)"
else
    echo -e "  上传文件: ${YELLOW}⚠️${NC} (未找到，可能为空)"
fi

if [ -n "$CHROMA_BACKUP" ]; then
    SIZE=$(du -h "$CHROMA_BACKUP" | cut -f1)
    echo -e "  向量数据库: ${GREEN}✅${NC} ($SIZE)"
else
    echo -e "  向量数据库: ${YELLOW}⚠️${NC} (未找到，可能为空)"
fi

echo ""
if [ "$BACKUP_VALID" = true ]; then
    echo -e "${GREEN}✅ 备份状态正常${NC}"
    log "备份状态检查通过"
    exit 0
else
    echo -e "${RED}❌ 备份状态异常${NC}"
    log "备份状态检查失败"
    exit 1
fi

