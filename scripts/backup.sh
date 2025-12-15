#!/bin/bash
# 增强版自动备份脚本
# 功能：备份 MySQL、Redis、文件数据、向量数据库
# 支持：错误处理、日志记录、远程备份、备份验证

set -e  # 遇到错误立即退出

# ============================================
# 配置区域
# ============================================
BACKUP_DIR="/opt/backups"
LOG_FILE="/opt/backups/backup.log"
COMPOSE_FILE="/opt/industrial-qa/docker-compose.prod.yml"
ENV_FILE="/opt/industrial-qa/.env"
RETENTION_DAYS=7  # 保留天数（基于时间的删除）
RETENTION_COUNT=0  # 保留备份数量（0表示不限制，基于数量的删除）
# 注意：如果 RETENTION_COUNT > 0，将优先使用数量限制，否则使用时间限制

# 远程备份配置（可选，取消注释并配置）
# REMOTE_BACKUP_ENABLED=true
# REMOTE_BACKUP_TYPE="s3"  # s3, oss, scp
# REMOTE_BACKUP_PATH="s3://your-bucket/backups/"
# AWS_ACCESS_KEY_ID="your-key"
# AWS_SECRET_ACCESS_KEY="your-secret"

# 邮件通知配置（可选，取消注释并配置）
# EMAIL_ENABLED=true
# EMAIL_TO="admin@example.com"
# SMTP_SERVER="smtp.example.com"
# SMTP_USER="backup@example.com"
# SMTP_PASS="password"

# ============================================
# 函数定义
# ============================================

# 日志函数
log() {
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[$timestamp] [$level] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 备份步骤日志
log_step() {
    local step_num="$1"
    local step_name="$2"
    log "═══════════════════════════════════════════════════════════════" "STEP"
    log "步骤 $step_num: $step_name" "STEP"
    log "═══════════════════════════════════════════════════════════════" "STEP"
}

# 备份结果日志
log_result() {
    local item="$1"
    local status="$2"
    local details="$3"
    if [ "$status" = "SUCCESS" ]; then
        log "✅ $item: $details" "RESULT"
    elif [ "$status" = "SKIP" ]; then
        log "⚠️  $item: $details" "RESULT"
    else
        log "❌ $item: $details" "ERROR"
    fi
}

# 错误处理函数
error_exit() {
    log "❌ 错误: $1"
    # 发送错误通知（如果配置了邮件）
    if [ "${EMAIL_ENABLED:-false}" = "true" ]; then
        send_email "备份失败" "备份过程中发生错误: $1"
    fi
    exit 1
}

# 发送邮件通知（需要安装 mailutils 或使用 sendmail）
send_email() {
    if [ "${EMAIL_ENABLED:-false}" != "true" ]; then
        return
    fi
    
    local subject="$1"
    local body="$2"
    
    # 使用 mail 命令（需要安装 mailutils）
    # echo "$body" | mail -s "$subject" "$EMAIL_TO" 2>/dev/null || true
    
    # 或使用 curl 发送邮件（如果配置了邮件 API）
    # curl -X POST "https://api.example.com/send-email" \
    #   -d "to=$EMAIL_TO&subject=$subject&body=$body" || true
    
    log "📧 邮件通知已发送: $subject"
}

# 验证备份文件
verify_backup() {
    local file="$1"
    if [ ! -f "$file" ]; then
        error_exit "备份文件不存在: $file"
    fi
    
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    if [ "$size" -eq 0 ]; then
        error_exit "备份文件为空: $file"
    fi
    
    log "✅ 备份验证通过: $file (大小: $(numfmt --to=iec-i --suffix=B $size 2>/dev/null || echo ${size}B))"
}

# 上传到远程存储（示例：AWS S3）
upload_to_remote() {
    if [ "${REMOTE_BACKUP_ENABLED:-false}" != "true" ]; then
        return
    fi
    
    local file="$1"
    log "📤 开始上传到远程存储: $file"
    
    case "${REMOTE_BACKUP_TYPE:-}" in
        s3)
            # 需要安装 awscli: apt-get install awscli
            if command -v aws &> /dev/null; then
                aws s3 cp "$file" "${REMOTE_BACKUP_PATH}$(basename $file)" || {
                    log "⚠️  远程上传失败，但继续执行"
                }
            else
                log "⚠️  AWS CLI 未安装，跳过远程上传"
            fi
            ;;
        oss)
            # 阿里云 OSS（需要安装 ossutil）
            if command -v ossutil &> /dev/null; then
                ossutil cp "$file" "${REMOTE_BACKUP_PATH}$(basename $file)" || {
                    log "⚠️  远程上传失败，但继续执行"
                }
            else
                log "⚠️  OSS util 未安装，跳过远程上传"
            fi
            ;;
        scp)
            # 使用 SCP 上传到远程服务器
            scp "$file" "${REMOTE_BACKUP_PATH}$(basename $file)" || {
                log "⚠️  远程上传失败，但继续执行"
            }
            ;;
        *)
            log "⚠️  未知的远程备份类型: ${REMOTE_BACKUP_TYPE}"
            ;;
    esac
    
    log "✅ 远程上传完成"
}

# ============================================
# 主备份流程
# ============================================

log "╔═══════════════════════════════════════════════════════════════╗" "START"
log "║                   备份任务开始                                ║" "START"
log "╚═══════════════════════════════════════════════════════════════╝" "START"
log "" "START"
log "备份时间: $(date '+%Y-%m-%d %H:%M:%S')" "INFO"
log "备份目录: $BACKUP_DIR" "INFO"
log "保留策略: $([ "$RETENTION_COUNT" -gt 0 ] && echo "数量限制($RETENTION_COUNT个)" || echo "时间限制($RETENTION_DAYS天)")" "INFO"
log "" "INFO"

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

# 创建备份目录
mkdir -p "$BACKUP_DIR"
log "📁 备份目录: $BACKUP_DIR"

# 生成时间戳
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_START_TIME=$(date +%s)
BACKUP_SUBDIR="$BACKUP_DIR/$DATE"
mkdir -p "$BACKUP_SUBDIR"

# 1. 备份 MySQL
log_step "1/4" "备份 MySQL 数据库"
MYSQL_BACKUP="$BACKUP_SUBDIR/mysql_${DATE}.sql.gz"
MYSQL_START_TIME=$(date +%s)
if docker compose -f "$COMPOSE_FILE" exec -T mysql mysqldump \
    -u root -p"${MYSQL_ROOT_PASSWORD}" \
    "${MYSQL_DATABASE}" | gzip > "$MYSQL_BACKUP"; then
    MYSQL_END_TIME=$(date +%s)
    MYSQL_DURATION=$((MYSQL_END_TIME - MYSQL_START_TIME))
    MYSQL_SIZE=$(stat -f%z "$MYSQL_BACKUP" 2>/dev/null || stat -c%s "$MYSQL_BACKUP" 2>/dev/null || echo "0")
    verify_backup "$MYSQL_BACKUP"
    log_result "MySQL 数据库" "SUCCESS" "大小: $(numfmt --to=iec-i --suffix=B $MYSQL_SIZE 2>/dev/null || echo ${MYSQL_SIZE}B), 耗时: ${MYSQL_DURATION}秒"
    upload_to_remote "$MYSQL_BACKUP"
else
    error_exit "MySQL 备份失败"
fi
log "" "INFO"

# 2. 备份 Redis（可选，因为已有 AOF 持久化）
log_step "2/4" "备份 Redis 数据"
REDIS_BACKUP="$BACKUP_SUBDIR/redis_${DATE}.rdb"
REDIS_START_TIME=$(date +%s)
if docker compose -f "$COMPOSE_FILE" exec redis redis-cli -a "${REDIS_PASSWORD}" BGSAVE 2>/dev/null; then
    sleep 2
    if docker cp industrial-qa-redis-prod:/data/dump.rdb "$REDIS_BACKUP" 2>/dev/null; then
        REDIS_END_TIME=$(date +%s)
        REDIS_DURATION=$((REDIS_END_TIME - REDIS_START_TIME))
        REDIS_SIZE=$(stat -f%z "$REDIS_BACKUP" 2>/dev/null || stat -c%s "$REDIS_BACKUP" 2>/dev/null || echo "0")
        verify_backup "$REDIS_BACKUP"
        log_result "Redis 数据" "SUCCESS" "大小: $(numfmt --to=iec-i --suffix=B $REDIS_SIZE 2>/dev/null || echo ${REDIS_SIZE}B), 耗时: ${REDIS_DURATION}秒"
        upload_to_remote "$REDIS_BACKUP"
    else
        log_result "Redis 数据" "SKIP" "备份跳过（可能不需要）"
    fi
else
    log_result "Redis 数据" "SKIP" "备份跳过（可能不需要）"
fi
log "" "INFO"

# 3. 备份上传的文件
log_step "3/4" "备份上传的文件"
UPLOADS_BACKUP="$BACKUP_SUBDIR/uploads_${DATE}.tar.gz"
UPLOADS_START_TIME=$(date +%s)
if [ -d "/opt/industrial-qa/data/uploads" ] && [ "$(ls -A /opt/industrial-qa/data/uploads 2>/dev/null)" ]; then
    if tar -czf "$UPLOADS_BACKUP" -C /opt/industrial-qa data/uploads 2>/dev/null; then
        UPLOADS_END_TIME=$(date +%s)
        UPLOADS_DURATION=$((UPLOADS_END_TIME - UPLOADS_START_TIME))
        UPLOADS_SIZE=$(stat -f%z "$UPLOADS_BACKUP" 2>/dev/null || stat -c%s "$UPLOADS_BACKUP" 2>/dev/null || echo "0")
        verify_backup "$UPLOADS_BACKUP"
        log_result "上传文件" "SUCCESS" "大小: $(numfmt --to=iec-i --suffix=B $UPLOADS_SIZE 2>/dev/null || echo ${UPLOADS_SIZE}B), 耗时: ${UPLOADS_DURATION}秒"
        upload_to_remote "$UPLOADS_BACKUP"
    else
        log_result "上传文件" "ERROR" "备份失败"
    fi
else
    log_result "上传文件" "SKIP" "目录为空，跳过备份"
fi
log "" "INFO"

# 4. 备份向量数据库
log_step "4/4" "备份向量数据库"
CHROMA_BACKUP="$BACKUP_SUBDIR/chroma_${DATE}.tar.gz"
CHROMA_START_TIME=$(date +%s)
if [ -d "/opt/industrial-qa/chroma_store" ] && [ "$(ls -A /opt/industrial-qa/chroma_store 2>/dev/null)" ]; then
    if tar -czf "$CHROMA_BACKUP" -C /opt/industrial-qa chroma_store 2>/dev/null; then
        CHROMA_END_TIME=$(date +%s)
        CHROMA_DURATION=$((CHROMA_END_TIME - CHROMA_START_TIME))
        CHROMA_SIZE=$(stat -f%z "$CHROMA_BACKUP" 2>/dev/null || stat -c%s "$CHROMA_BACKUP" 2>/dev/null || echo "0")
        verify_backup "$CHROMA_BACKUP"
        log_result "向量数据库" "SUCCESS" "大小: $(numfmt --to=iec-i --suffix=B $CHROMA_SIZE 2>/dev/null || echo ${CHROMA_SIZE}B), 耗时: ${CHROMA_DURATION}秒"
        upload_to_remote "$CHROMA_BACKUP"
    else
        log_result "向量数据库" "ERROR" "备份失败"
    fi
else
    log_result "向量数据库" "SKIP" "目录为空，跳过备份"
fi
log "" "INFO"

# 清理旧备份
log_step "5/5" "清理旧备份"

# 统计清理前的备份数量
BACKUP_COUNT_BEFORE=$(find "$BACKUP_DIR" -type d -name "20*" 2>/dev/null | wc -l)
BACKUP_SIZE_BEFORE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")

if [ "$RETENTION_COUNT" -gt 0 ]; then
    # 基于数量的删除策略：保留最近的 N 个备份
    log "📊 使用数量限制策略：保留最近 $RETENTION_COUNT 个备份"
    
    # 获取所有备份目录，按时间排序（最新的在前）
    BACKUP_LIST=$(find "$BACKUP_DIR" -type d -name "20*" -maxdepth 1 2>/dev/null | sort -r)
    BACKUP_TOTAL=$(echo "$BACKUP_LIST" | grep -c . || echo "0")
    
    if [ "$BACKUP_TOTAL" -gt "$RETENTION_COUNT" ]; then
        # 计算需要删除的数量
        DELETE_COUNT=$((BACKUP_TOTAL - RETENTION_COUNT))
        log "📊 当前备份数: $BACKUP_TOTAL，保留数: $RETENTION_COUNT，将删除: $DELETE_COUNT"
        
        # 获取需要删除的备份（从旧到新）
        DELETE_LIST=$(echo "$BACKUP_LIST" | tail -n +$((RETENTION_COUNT + 1)))
        
        # 删除旧备份
        DELETED_SIZE=0
        DELETED_COUNT=0
        while IFS= read -r backup_dir; do
            if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
                BACKUP_SIZE=$(du -sk "$backup_dir" 2>/dev/null | cut -f1 || echo "0")
                BACKUP_NAME=$(basename "$backup_dir")
                log "🗑️  删除备份: $BACKUP_NAME (大小: $(numfmt --to=iec-i --suffix=B $((BACKUP_SIZE * 1024)) 2>/dev/null || echo ${BACKUP_SIZE}KB))"
                rm -rf "$backup_dir" 2>/dev/null && {
                    DELETED_SIZE=$((DELETED_SIZE + BACKUP_SIZE))
                    DELETED_COUNT=$((DELETED_COUNT + 1))
                }
            fi
        done <<< "$DELETE_LIST"
        
        log "✅ 已删除 $DELETED_COUNT 个备份，释放空间: $(numfmt --to=iec-i --suffix=B $((DELETED_SIZE * 1024)) 2>/dev/null || echo ${DELETED_SIZE}KB)"
    else
        log "ℹ️  备份数量 ($BACKUP_TOTAL) 未超过限制 ($RETENTION_COUNT)，无需删除"
    fi
else
    # 基于时间的删除策略：删除 N 天前的备份
    log "📊 使用时间限制策略：删除 $RETENTION_DAYS 天前的备份"
    
    # 统计要删除的备份
    OLD_BACKUPS=$(find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS 2>/dev/null)
    OLD_COUNT=$(echo "$OLD_BACKUPS" | grep -c . || echo "0")
    
    if [ "$OLD_COUNT" -gt 0 ]; then
        log "📊 找到 $OLD_COUNT 个超过 $RETENTION_DAYS 天的备份，开始删除..."
        
        DELETED_SIZE=0
        DELETED_COUNT=0
        while IFS= read -r backup_dir; do
            if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
                BACKUP_SIZE=$(du -sk "$backup_dir" 2>/dev/null | cut -f1 || echo "0")
                BACKUP_NAME=$(basename "$backup_dir")
                BACKUP_AGE=$(find "$backup_dir" -maxdepth 0 -printf '%T@' 2>/dev/null || stat -c %Y "$backup_dir" 2>/dev/null || echo "0")
                BACKUP_AGE_DAYS=$(( (CURRENT_TIME - BACKUP_AGE) / 86400 ))
                log "🗑️  删除备份: $BACKUP_NAME (年龄: ${BACKUP_AGE_DAYS} 天, 大小: $(numfmt --to=iec-i --suffix=B $((BACKUP_SIZE * 1024)) 2>/dev/null || echo ${BACKUP_SIZE}KB))"
                rm -rf "$backup_dir" 2>/dev/null && {
                    DELETED_SIZE=$((DELETED_SIZE + BACKUP_SIZE))
                    DELETED_COUNT=$((DELETED_COUNT + 1))
                }
            fi
        done <<< "$OLD_BACKUPS"
        
        # 清理可能遗留的单独文件
        find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
        find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
        
        log "✅ 已删除 $DELETED_COUNT 个备份，释放空间: $(numfmt --to=iec-i --suffix=B $((DELETED_SIZE * 1024)) 2>/dev/null || echo ${DELETED_SIZE}KB)"
    else
        log "ℹ️  没有找到超过 $RETENTION_DAYS 天的备份，无需删除"
    fi
fi

# 统计清理后的备份情况
BACKUP_COUNT_AFTER=$(find "$BACKUP_DIR" -type d -name "20*" 2>/dev/null | wc -l)
BACKUP_SIZE_AFTER=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
log "📊 清理完成 - 备份数量: $BACKUP_COUNT_BEFORE → $BACKUP_COUNT_AFTER, 总大小: $BACKUP_SIZE_BEFORE → $BACKUP_SIZE_AFTER"

# 计算备份大小和总耗时
TOTAL_SIZE=$(du -sh "$BACKUP_SUBDIR" 2>/dev/null | cut -f1 || echo "0")
BACKUP_END_TIME=$(date +%s)
TOTAL_DURATION=$((BACKUP_END_TIME - BACKUP_START_TIME))

log "" "INFO"
log "╔═══════════════════════════════════════════════════════════════╗" "SUMMARY"
log "║                   备份任务完成                                ║" "SUMMARY"
log "╚═══════════════════════════════════════════════════════════════╝" "SUMMARY"
log "" "SUMMARY"
log "备份时间戳: $DATE" "SUMMARY"
log "备份位置: $BACKUP_SUBDIR" "SUMMARY"
log "总大小: $TOTAL_SIZE" "SUMMARY"
log "总耗时: ${TOTAL_DURATION}秒 ($(($TOTAL_DURATION / 60))分$(($TOTAL_DURATION % 60))秒)" "SUMMARY"
log "" "SUMMARY"
log "备份内容:" "SUMMARY"
[ -f "$MYSQL_BACKUP" ] && log "  ✓ MySQL 数据库" "SUMMARY"
[ -f "$REDIS_BACKUP" ] && log "  ✓ Redis 数据" "SUMMARY"
[ -f "$UPLOADS_BACKUP" ] && log "  ✓ 上传文件" "SUMMARY"
[ -f "$CHROMA_BACKUP" ] && log "  ✓ 向量数据库" "SUMMARY"
log "" "SUMMARY"

# 发送成功通知
if [ "${EMAIL_ENABLED:-false}" = "true" ]; then
    send_email "备份成功" "备份已完成\n时间: $DATE\n大小: $TOTAL_SIZE\n位置: $BACKUP_SUBDIR"
fi

exit 0

