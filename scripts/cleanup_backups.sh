#!/bin/bash
# 独立的备份清理脚本
# 可以单独运行，用于手动清理或作为独立的定时任务

set -e

# ============================================
# 配置区域
# ============================================
BACKUP_DIR="/opt/backups"
LOG_FILE="/opt/backups/cleanup.log"
RETENTION_DAYS=7  # 保留天数（基于时间的删除）
RETENTION_COUNT=0  # 保留备份数量（0表示不限制，基于数量的删除）

# ============================================
# 函数定义
# ============================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============================================
# 主清理流程
# ============================================

log "=========================================="
log "🧹 开始清理旧备份"
log "=========================================="

# 检查备份目录
if [ ! -d "$BACKUP_DIR" ]; then
    log "❌ 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 统计清理前的备份数量
BACKUP_COUNT_BEFORE=$(find "$BACKUP_DIR" -type d -name "20*" 2>/dev/null | wc -l)
BACKUP_SIZE_BEFORE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
CURRENT_TIME=$(date +%s)

log "📊 清理前统计:"
log "  备份数量: $BACKUP_COUNT_BEFORE"
log "  总大小: $BACKUP_SIZE_BEFORE"

if [ "$RETENTION_COUNT" -gt 0 ]; then
    # 基于数量的删除策略
    log "📊 使用数量限制策略：保留最近 $RETENTION_COUNT 个备份"
    
    BACKUP_LIST=$(find "$BACKUP_DIR" -type d -name "20*" -maxdepth 1 2>/dev/null | sort -r)
    BACKUP_TOTAL=$(echo "$BACKUP_LIST" | grep -c . || echo "0")
    
    if [ "$BACKUP_TOTAL" -gt "$RETENTION_COUNT" ]; then
        DELETE_COUNT=$((BACKUP_TOTAL - RETENTION_COUNT))
        log "📊 当前备份数: $BACKUP_TOTAL，保留数: $RETENTION_COUNT，将删除: $DELETE_COUNT"
        
        DELETE_LIST=$(echo "$BACKUP_LIST" | tail -n +$((RETENTION_COUNT + 1)))
        
        DELETED_SIZE=0
        DELETED_COUNT=0
        while IFS= read -r backup_dir; do
            if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
                BACKUP_SIZE=$(du -sk "$backup_dir" 2>/dev/null | cut -f1 || echo "0")
                BACKUP_NAME=$(basename "$backup_dir")
                log "🗑️  删除备份: $BACKUP_NAME"
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
    # 基于时间的删除策略
    log "📊 使用时间限制策略：删除 $RETENTION_DAYS 天前的备份"
    
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
                BACKUP_AGE=$(stat -c %Y "$backup_dir" 2>/dev/null || stat -f %m "$backup_dir" 2>/dev/null || echo "0")
                BACKUP_AGE_DAYS=$(( (CURRENT_TIME - BACKUP_AGE) / 86400 ))
                log "🗑️  删除备份: $BACKUP_NAME (年龄: ${BACKUP_AGE_DAYS} 天)"
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

log "=========================================="
log "📊 清理完成统计:"
log "  备份数量: $BACKUP_COUNT_BEFORE → $BACKUP_COUNT_AFTER"
log "  总大小: $BACKUP_SIZE_BEFORE → $BACKUP_SIZE_AFTER"
log "=========================================="

exit 0

