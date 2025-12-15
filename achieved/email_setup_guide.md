# 邮箱功能配置和使用指南

## 概述

项目已实现完整的邮箱功能，包括：
- ✅ 邮箱验证（注册后发送验证码）
- ✅ 重新发送验证码
- ✅ 忘记密码（发送重置链接）
- ✅ 重置密码

**验证方式**: 使用6位数字验证码，5分钟内有效（无需前端页面）

## 技术实现

- **服务商**: 阿里云邮件推送（DirectMail）
- **方式**: SMTP
- **免费额度**: 每天 200 封（需实名认证）
- **超出费用**: 约 ¥0.01/封

## 配置步骤

### 1. 开通阿里云邮件推送服务

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 搜索并开通"邮件推送"服务
3. 完成实名认证（必需，否则无法使用）
4. 配置发信域名（需要 DNS 验证）
5. 设置发信地址（如 `noreply@yourdomain.com`）
6. 在控制台设置 SMTP 密码

### 2. 配置环境变量

编辑 `.env` 文件，添加以下配置：

```bash
# Email (Aliyun DirectMail)
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_REGION=cn-hangzhou
ALIYUN_SMTP_PASSWORD=your-smtp-password  # 在阿里云控制台设置

# 发信地址（必须在阿里云控制台配置）
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Industrial QA System

# 前端URL（可选，用于密码重置链接，验证码方式不需要）
FRONTEND_URL=https://yourdomain.com
```

### 3. 验证配置

```bash
# 重启服务后，检查配置是否正确加载
docker compose -f docker-compose.prod.yml logs app | grep -i email
```

## 功能说明

### 1. 邮箱验证流程

#### 注册时自动发送验证码

如果配置了 `ALIYUN_SMTP_PASSWORD`，用户注册后：
1. 系统自动发送6位数字验证码到注册邮箱
2. 用户初始状态为 `is_verified=false`
3. 用户查看邮件获取验证码
4. 用户调用验证接口输入验证码完成验证
5. 系统验证验证码并标记邮箱为已验证

#### 手动触发验证码

如果用户没有收到验证码或验证码已过期，可以调用重新发送接口：

```bash
POST /api/v1/resend-verification
{
  "email": "user@example.com"
}
```

验证码5分钟内有效。

### 2. 密码重置流程

#### 忘记密码

```bash
POST /api/v1/forgot-password
{
  "email": "user@example.com"
}
```

系统会发送密码重置链接到注册邮箱，链接1小时内有效。

#### 重置密码

```bash
POST /api/v1/reset-password
{
  "token": "reset-token-from-email",
  "new_password": "new_password_123"
}
```

使用邮件中的 token 重置密码。

## API 接口

### 1. 验证邮箱

**端点**: `POST /api/v1/verify-email`

**请求**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "verified": true,
    "message": "Email verified successfully"
  }
}
```

**说明**: 
- `code`: 6位数字验证码，从邮件中获取
- 验证码5分钟内有效
- 如果验证码无效或过期，返回 400 错误

### 2. 重新发送验证码

**端点**: `POST /api/v1/resend-verification`

**请求**:
```json
{
  "email": "user@example.com"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message": "If the email exists and is not verified, a verification code has been sent"
  }
}
```

**说明**: 
- 重新发送6位数字验证码到指定邮箱
- 验证码5分钟内有效

### 3. 忘记密码

**端点**: `POST /api/v1/forgot-password`

**请求**:
```json
{
  "email": "user@example.com"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message": "If the email exists, a password reset link has been sent"
  }
}
```

### 4. 重置密码

**端点**: `POST /api/v1/reset-password`

**请求**:
```json
{
  "token": "reset-token-from-email",
  "new_password": "new_password_123"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message": "Password reset successfully"
  }
}
```

## 邮件模板

### 验证码邮件

- **主题**: "验证您的邮箱 - 工业问答系统"
- **内容**: HTML 格式，显示6位数字验证码
- **有效期**: 5 分钟

### 密码重置邮件

- **主题**: "重置您的密码 - 工业问答系统"
- **内容**: HTML 格式，包含重置按钮和链接
- **有效期**: 1 小时

## 安全特性

1. **防止邮箱枚举**: 
   - 即使用户不存在，也返回成功消息
   - 防止攻击者通过接口枚举已注册邮箱

2. **验证码安全**:
   - 使用6位随机数字生成验证码
   - 验证码存储在 Redis 中，5分钟有效
   - 验证后立即删除验证码
   - 支持重新发送，每次发送新的验证码

3. **错误处理**:
   - 邮件发送失败不影响注册流程
   - 详细的错误日志记录

## 测试邮箱功能

### 1. 测试注册和验证

```bash
# 1. 注册用户
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "username": "testuser",
    "full_name": "Test User"
  }'

# 2. 检查邮箱（应该收到验证码邮件）
# 从邮件中获取6位数字验证码，例如：123456

# 3. 验证邮箱
curl -X POST http://localhost:8000/api/v1/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'
```

### 2. 测试密码重置

```bash
# 1. 请求密码重置
curl -X POST http://localhost:8000/api/v1/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'

# 2. 检查邮箱（应该收到重置邮件）
# 从邮件中获取 token

# 3. 重置密码
curl -X POST http://localhost:8000/api/v1/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-reset-token",
    "new_password": "new_password_123"
  }'
```

## 故障排查

### 邮件发送失败

1. **检查配置**:
   ```bash
   # 确认环境变量已正确设置
   docker compose -f docker-compose.prod.yml exec app env | grep ALIYUN
   ```

2. **检查日志**:
   ```bash
   # 查看应用日志
   docker compose -f docker-compose.prod.yml logs app | grep -i email
   ```

3. **常见问题**:
   - SMTP 密码错误
   - 发信地址未在阿里云控制台配置
   - 域名未验证
   - 超出免费额度（每天 200 封）

### 验证码验证失败

1. **检查 Redis**:
   ```bash
   # 检查验证码是否在 Redis 中
   docker compose -f docker-compose.prod.yml exec redis redis-cli
   # 在 Redis CLI 中执行: KEYS email_verification_code:*
   # 或: KEYS password_reset:*
   ```

2. **检查过期时间**:
   - 邮箱验证码: 5 分钟
   - 密码重置 token: 1 小时

3. **常见问题**:
   - 验证码已过期（超过5分钟）
   - 验证码输入错误
   - 验证码已被使用（验证后会自动删除）

### 邮件未收到

1. **检查垃圾邮件文件夹**
2. **确认发信地址已配置**
3. **检查阿里云控制台的发送记录**
4. **确认域名 DNS 配置正确**

## 禁用邮箱功能

如果不想使用邮箱功能，只需不配置 `ALIYUN_SMTP_PASSWORD`：

```bash
# 在 .env 中留空或注释掉
# ALIYUN_SMTP_PASSWORD=
```

这样：
- 用户注册后自动标记为已验证（`is_verified=true`）
- 邮箱验证相关接口返回 503 错误
- 密码重置功能不可用

## 最佳实践

1. **生产环境**:
   - 使用自己的域名配置发信地址
   - 设置合理的邮件发送频率限制
   - 监控邮件发送失败情况

2. **开发环境**:
   - 可以使用测试邮箱服务
   - 或直接禁用邮箱验证（不配置 SMTP 密码）

3. **安全建议**:
   - 定期更换 SMTP 密码
   - 限制密码重置请求频率
   - 监控异常登录尝试

## 相关文档

- API 文档: `achieved/api.md`
- 部署指南: `achieved/production_deployment_guide.md`
- 邮箱服务选型: `Doc/Selection/09_email_service.md`

