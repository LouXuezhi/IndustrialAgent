# 备份脚本使用说明

## 概述

本项目提供了完整的自动化备份解决方案，包括：
- `backup.sh`: 自动备份脚本
- `restore_backup.sh`: 备份恢复脚本
- `check_backup.sh`: 备份状态检查脚本

## 快速开始

### 1. 部署备份脚本

```bash
# 在服务器上执行
cd /opt/industrial-qa

# 创建备份目录
sudo mkdir -p /opt/backups
sudo chown $USER:$USER /opt/backups

# 复制脚本
cp scripts/backup.sh /opt/backups/backup.sh
cp scripts/restore_backup.sh /opt/backups/restore_backup.sh
cp scripts/check_backup.sh /opt/backups/check_backup.sh

# 设置执行权限
chmod +x /opt/backups/*.sh
```

### 2. 配置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点执行备份）
0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1

# 可选：每小时检查备份状态
0 * * * * /opt/backups/check_backup.sh >> /opt/backups/backup_check.log 2>&1
```

### 3. 测试备份

```bash
# 手动执行备份
/opt/backups/backup.sh

# 检查备份状态
/opt/backups/check_backup.sh

# 查看备份日志
tail -f /opt/backups/backup.log
```

## 脚本功能

### backup.sh - 自动备份脚本

**功能**:
- ✅ 备份 MySQL 数据库（压缩格式）
- ✅ 备份 Redis 数据（RDB 文件）
- ✅ 备份上传的文件
- ✅ 备份向量数据库（ChromaDB）
- ✅ 自动验证备份文件完整性
- ✅ 自动清理旧备份（默认保留 7 天）
- ✅ 支持远程备份（S3/OSS/SCP，可选）
- ✅ 支持邮件通知（可选）

**配置选项**:
编辑 `/opt/backups/backup.sh` 可以修改：
- `RETENTION_DAYS`: 备份保留天数（默认 7 天，基于时间的删除）
- `RETENTION_COUNT`: 保留备份数量（默认 0，0表示不限制，基于数量的删除）
  - 如果 `RETENTION_COUNT > 0`，将优先使用数量限制
  - 如果 `RETENTION_COUNT = 0`，使用时间限制（`RETENTION_DAYS`）
- `REMOTE_BACKUP_ENABLED`: 启用远程备份
- `REMOTE_BACKUP_TYPE`: 远程备份类型（s3/oss/scp）
- `EMAIL_ENABLED`: 启用邮件通知

**删除策略说明**:
- **基于时间**: 删除超过 N 天的备份（`RETENTION_COUNT = 0`）
- **基于数量**: 只保留最近的 N 个备份（`RETENTION_COUNT > 0`）
- 删除时会显示每个备份的年龄和大小
- 删除前会统计，删除后会显示释放的空间

### restore_backup.sh - 备份恢复脚本

**用法**:
```bash
# 查看可用备份
/opt/backups/restore_backup.sh

# 恢复指定备份
/opt/backups/restore_backup.sh 20241215_020000
```

**功能**:
- ✅ 恢复 MySQL 数据库
- ✅ 恢复上传的文件
- ✅ 恢复向量数据库
- ✅ 恢复 Redis 数据（可选）
- ✅ 安全确认提示

### cleanup_backups.sh - 独立清理脚本

**用法**:
```bash
# 手动清理旧备份（不执行备份）
/opt/backups/cleanup_backups.sh
```

**功能**:
- ✅ 独立的清理脚本，可以单独运行
- ✅ 支持基于时间或数量的删除策略
- ✅ 详细的删除日志
- ✅ 删除前后统计信息

**使用场景**:
- 作为独立的定时任务，在非备份时间清理
- 手动清理磁盘空间
- 测试清理策略

### check_backup.sh - 备份状态检查脚本

**用法**:
```bash
/opt/backups/check_backup.sh
```

**功能**:
- ✅ 检查最新备份时间
- ✅ 验证备份文件完整性
- ✅ 检查备份是否过期（默认 25 小时）
- ✅ 显示备份文件大小

## 定时任务配置示例

### 每天备份一次（推荐）

```bash
# 每天凌晨 2 点执行
0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

### 每天备份两次

```bash
# 每天凌晨 2 点和下午 2 点执行
0 2,14 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

### 每周完整备份 + 每天增量备份

```bash
# 每周日凌晨 3 点完整备份
0 3 * * 0 /opt/backups/backup.sh full >> /opt/backups/backup.log 2>&1

# 每天凌晨 2 点增量备份
0 2 * * 1-6 /opt/backups/backup.sh incremental >> /opt/backups/backup.log 2>&1
```

### 每小时备份（高频场景）

```bash
# 每小时执行一次（谨慎使用，会产生大量备份）
0 * * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

## 备份目录结构

```
/opt/backups/
├── backup.log                    # 备份日志
├── backup_check.log              # 备份检查日志
├── 20241215_020000/              # 备份目录（按时间戳命名）
│   ├── mysql_20241215_020000.sql.gz
│   ├── redis_20241215_020000.rdb
│   ├── uploads_20241215_020000.tar.gz
│   └── chroma_20241215_020000.tar.gz
├── 20241216_020000/
│   └── ...
└── ...
```

## 远程备份配置

### AWS S3 备份

```bash
# 1. 安装 AWS CLI
sudo apt-get install awscli

# 2. 配置凭证
aws configure

# 3. 编辑 backup.sh，取消注释并配置：
REMOTE_BACKUP_ENABLED=true
REMOTE_BACKUP_TYPE="s3"
REMOTE_BACKUP_PATH="s3://your-bucket/industrial-qa/backups/"
```

### 阿里云 OSS 备份

```bash
# 1. 下载 ossutil
wget https://gosspublic.alicdn.com/ossutil/1.7.14/ossutil64
chmod +x ossutil64
sudo mv ossutil64 /usr/local/bin/ossutil

# 2. 配置
ossutil config

# 3. 编辑 backup.sh，取消注释并配置：
REMOTE_BACKUP_ENABLED=true
REMOTE_BACKUP_TYPE="oss"
REMOTE_BACKUP_PATH="oss://your-bucket/backups/"
```

## 邮件通知配置

```bash
# 1. 安装邮件工具（Ubuntu/Debian）
sudo apt-get install mailutils

# 2. 编辑 backup.sh，取消注释并配置：
EMAIL_ENABLED=true
EMAIL_TO="admin@example.com"
```

## 故障排查

### 备份失败

```bash
# 查看详细日志
tail -100 /opt/backups/backup.log

# 检查环境变量
source /opt/industrial-qa/.env
echo $MYSQL_ROOT_PASSWORD

# 测试 MySQL 连接
docker compose -f /opt/industrial-qa/docker-compose.prod.yml exec mysql mysqladmin ping -h localhost
```

### 恢复失败

```bash
# 检查备份文件是否存在
ls -lh /opt/backups/20241215_020000/

# 验证备份文件完整性
gunzip -t /opt/backups/20241215_020000/mysql_*.sql.gz
tar -tzf /opt/backups/20241215_020000/uploads_*.tar.gz
```

### 定时任务不执行

```bash
# 检查 crontab
crontab -l

# 检查 cron 服务状态
sudo systemctl status cron  # Ubuntu/Debian
sudo systemctl status crond # CentOS/RHEL

# 查看系统日志
sudo tail -f /var/log/syslog | grep CRON  # Ubuntu/Debian
sudo tail -f /var/log/cron                 # CentOS/RHEL
```

## 最佳实践

1. **定期测试恢复**: 每月至少测试一次备份恢复流程
2. **监控备份状态**: 设置备份检查定时任务，及时发现问题
3. **远程备份**: 生产环境建议配置远程备份，防止本地数据丢失
4. **保留策略**: 根据数据重要性调整保留天数
5. **日志监控**: 定期检查备份日志，确保备份成功

## 备份策略建议

| 场景 | 备份频率 | 保留时间 | 说明 |
|------|---------|---------|------|
| 生产环境 | 每天 1-2 次 | 7-30 天 | 平衡存储和恢复需求 |
| 重要数据 | 每小时 | 7 天 | 高频备份 |
| 开发环境 | 每周 | 7 天 | 低频备份 |
| 测试环境 | 手动 | 3 天 | 按需备份 |

## 相关文档

- 详细部署指南: `achieved/production_deployment_guide.md`
- API 文档: `achieved/api.md`

