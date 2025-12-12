# 邮件服务选型：阿里云邮件推送

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定

## 选型结果

**选择**: 阿里云邮件推送  
**服务商**: 阿里云  
**免费额度**: 每天200封（需实名认证）  
**超出费用**: 约 ¥0.01/封

## 技术特性

- **国内服务**: 数据合规，适合国内应用
- **稳定可靠**: 高送达率，服务稳定
- **易于集成**: 提供Python SDK，集成简单
- **成本合理**: 有免费额度，超出后按量付费

## 项目中的实现

### 依赖安装

```bash
pip install aliyun-python-sdk-core aliyun-python-sdk-dm
```

或添加到 `pyproject.toml`：

```toml
dependencies = [
    "aliyun-python-sdk-core>=2.14.0",
    "aliyun-python-sdk-dm>=3.3.0",
]
```

### 配置示例

```python
# app/core/config.py
class Settings(BaseSettings):
    # 阿里云邮件推送配置
    aliyun_access_key_id: str = Field(default="")
    aliyun_access_key_secret: str = Field(default="")
    aliyun_region: str = Field(default="cn-hangzhou")
    from_email: str = Field(default="noreply@example.com")
    from_name: str = Field(default="Industrial QA System")
    frontend_url: str = Field(default="http://localhost:3000")
```

### 环境变量配置

```bash
# .env
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_REGION=cn-hangzhou
FROM_EMAIL=noreply@example.com
FROM_NAME=Industrial QA System
FRONTEND_URL=http://localhost:3000
```

### 实现示例

```python
# app/core/email.py
from aliyunsdkcore.client import AcsClient
from aliyunsdkdm.request.v20151123 import SingleSendMailRequest
from app.core.config import Settings

class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AcsClient(
            settings.aliyun_access_key_id,
            settings.aliyun_access_key_secret,
            settings.aliyun_region
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """发送邮件"""
        try:
            request = SingleSendMailRequest.SingleSendMailRequest()
            request.set_AccountName(self.settings.from_email)
            request.set_FromAlias(self.settings.from_name)
            request.set_ToAddress(to_email)
            request.set_Subject(subject)
            request.set_HtmlBody(html_content)
            
            response = self.client.do_action_with_exception(request)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
```

## 使用场景

### 1. 邮箱验证
- 用户注册后发送验证邮件
- 验证链接24小时有效
- 使用Redis存储验证令牌

### 2. 密码重置
- 用户请求重置密码时发送邮件
- 重置链接1小时有效

### 3. 通知邮件
- 系统通知
- 重要操作提醒

## 配置步骤

### 1. 开通服务
1. 登录阿里云控制台
2. 开通"邮件推送"服务
3. 完成实名认证（获取免费额度）

### 2. 配置发信地址
1. 在邮件推送控制台添加发信地址
2. 验证域名或邮箱
3. 获取发信地址（用于 `FROM_EMAIL` 配置）

### 3. 获取AccessKey
1. 在阿里云控制台创建AccessKey
2. 获取 AccessKey ID 和 AccessKey Secret
3. 配置到环境变量

## 费用说明

- **免费额度**: 每天200封（需实名认证）
- **超出费用**: 约 ¥0.01/封
- **适用场景**: 国内生产环境，中小到大规模应用

## 注意事项

1. **发信地址验证**: 必须在阿里云控制台配置并验证发信地址
2. **频率限制**: 注意发送频率限制，避免触发反垃圾邮件机制
3. **内容规范**: 邮件内容需符合规范，避免被标记为垃圾邮件
4. **错误处理**: 妥善处理发送失败的情况，记录日志并重试

## 参考资源

- [阿里云邮件推送文档](https://help.aliyun.com/product/29412.html)
- [Python SDK文档](https://help.aliyun.com/document_detail/29444.html)



