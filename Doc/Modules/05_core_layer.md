# 核心层模块文档

## 概述
核心层提供应用的基础设施功能，包括配置管理、安全验证和日志记录。这些模块被其他层广泛使用，是系统的基石。

## 模块结构

```
app/core/
├── config.py      # 配置管理
├── security.py    # 安全验证
├── logging.py     # 日志配置
└── email.py       # 邮件发送服务
```

## 1. 配置管理 (`config.py`)

### 功能
使用Pydantic Settings管理应用配置，支持环境变量和配置文件。

### 类定义（现状要点）

- 敏感值默认空字符串，必须通过环境变量或 `.env` 注入。
- 关键新增：`database_url`（MySQL）、`redis_url`、`jwt_secret`、`storage_dir`、DashScope/OpenAI 多套 API Key（embedding/LLM 可分离）。
- 详见代码 `app/core/config.py`。

### 配置项说明（节选）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `app_name` | "Industrial QA Backend" | 应用名称 |
| `app_env` | "local" | 环境（local/dev/prod） |
| `database_url` | "" | MySQL 连接串，必须注入 |
| `redis_url` | "" | Redis 连接串，用于 JWT 黑名单等 |
| `jwt_secret` | "" | JWT 密钥，必须注入 |
| `jwt_algorithm` | "HS256" | JWT 算法 |
| `access_token_expires_minutes` | 60 | 访问 token 过期时间 |
| `vector_db_uri` | `chroma://./chroma_store` | 向量库 URI |
| `storage_dir` | `data/uploads` | 原始文件持久化目录 |
| `embedding_model` | "bge-large" | 默认 embedding 模型名 |
| `llm_provider` | "openai" | LLM 提供商（openai/dashscope） |
| `llm_model` | "gpt-4o-mini" | 默认 LLM 模型 |
| `openai_api_key` | "" | OpenAI Key |
| `dashscope_embedding_api_key` | "" | DashScope embedding Key（可与 LLM 分离） |
| `dashscope_llm_api_key` | "" | DashScope LLM Key |
| `dashscope_*_base_url` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | DashScope 兼容模式 Base URL，可按区域调整 |
| `allowed_origins` | ["*"] | CORS |
| `telemetry_sample_rate` | 0.0 | 遥测采样率 |
| 邮件相关 | 见 `aliyun_*`、`from_email`、`from_name` | 阿里云邮件推送 |

### 配置加载机制

1. **环境变量优先**: 从 `.env` 文件或系统环境变量读取
2. **默认值回退**: 如果环境变量不存在，使用Field中的默认值
3. **类型验证**: Pydantic自动进行类型验证和转换
4. **缓存**: 使用 `@lru_cache` 装饰器缓存Settings实例

### 使用方式

#### 方式1: 直接导入（推荐）
```python
from app.core.config import settings

db_url = settings.database_url
api_key = settings.openai_api_key
```

#### 方式2: 依赖注入（FastAPI）
```python
from app.core.config import get_settings, Settings

def my_endpoint(settings: Settings = Depends(get_settings)):
    return {"db_url": settings.database_url}
```

### 环境变量配置（示例，需按环境覆盖）

```bash
# 基础
APP_ENV=production
APP_NAME=Industrial QA Backend

# 数据库 / 缓存
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/industrial_qa
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=please-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=60

# 存储与向量库
STORAGE_DIR=data/uploads
VECTOR_DB_URI=chroma://./chroma_store

# 模型与钥匙（OpenAI 或 DashScope 任选其一，embedding/LLM 可分钥）
LLM_PROVIDER=openai            # 或 dashscope
EMBEDDING_MODEL=bge-large
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=
DASHSCOPE_API_KEY=            # 兼容模式通用 Key（可选）
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_EMBEDDING_API_KEY=
DASHSCOPE_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_LLM_API_KEY=
DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 邮件（阿里云）
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_REGION=cn-hangzhou
FROM_EMAIL=noreply@example.com
FROM_NAME=Industrial QA System
FRONTEND_URL=http://localhost:3000
```

### 配置扩展

添加新配置项：
```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 新增配置
    redis_url: str = Field(default="redis://localhost:6379")
    max_query_length: int = Field(default=1000, ge=100, le=10000)
    enable_cache: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 配置验证

Pydantic自动进行验证：
- 类型检查
- 约束验证（如 `ge`, `le` 用于数值范围）
- 自定义验证器

示例：
```python
from pydantic import validator

class Settings(BaseSettings):
    port: int = Field(default=8000)
    
    @validator('port')
    def validate_port(cls, v):
        if not (1024 <= v <= 65535):
            raise ValueError('Port must be between 1024 and 65535')
        return v
```

## 2. 安全验证 (`security.py`)

### 功能
- 采用 JWT 取代 API Key，所有访问需携带 `Authorization: Bearer <token>`。
- Redis 维护黑名单/注销列表，通过 `jti` 检查是否被吊销。
- 登录/刷新时生成带 `jti` 的 access token；注销时将 `jti` 写入 Redis，TTL 与 token 过期保持一致。

### 核心逻辑（概述）
- `create_access_token`：生成包含 `sub`、`jti`、`exp` 等声明的 JWT。
- `revoke_token`：将 `TOKEN_BLACKLIST_PREFIX + jti` 写入 Redis，设置到期 TTL。
- `get_current_user`：解码 JWT，校验签名/过期，再检查 Redis 黑名单，若命中则 401。

### 依赖与配置
- 依赖 `jwt_secret`、`jwt_algorithm`、`access_token_expires_minutes`。
- Redis 通过 `redis_url` 连接；异常时可按需选择“失败兜底允许”或“严格拒绝”策略（当前实现兜底允许）。

### 使用方式
- 在路由上使用 `Depends(get_current_user)` 获取当前用户并完成鉴权。
- `/auth/login`、`/auth/refresh` 返回带 `jti` 的 token；`/auth/logout` 将当前 token 注销。

## 3. 日志配置 (`logging.py`)

### 功能
配置应用日志系统，提供结构化日志输出。

### 实现

```python
import logging
import sys

def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured logging once at startup."""
    if logging.getLogger().handlers:
        return  # 避免重复配置
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
```

### 日志格式

当前格式: `时间戳 | 级别 | 模块名 | 消息`

示例输出:
```
2024-01-15 10:30:45 | INFO | app.main | Application started
2024-01-15 10:30:46 | ERROR | app.rag.pipeline | Failed to retrieve documents
```

### 使用方式

#### 在模块中使用
```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Function started")
    try:
        # 业务逻辑
        logger.debug("Processing data")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
```

#### 在应用启动时配置
```python
# app/main.py
from app.core.logging import configure_logging

configure_logging(level=logging.INFO)
app = FastAPI(...)
```

### 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认级别）
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 日志增强建议

#### 1. 结构化日志（JSON格式）
```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler.setFormatter(JSONFormatter())
```

#### 2. 文件日志
```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
root.addHandler(file_handler)
```

#### 3. 环境特定配置
```python
def configure_logging(level: int | None = None):
    if level is None:
        level = logging.DEBUG if settings.app_env == "local" else logging.INFO
    
    # ... 配置逻辑
```

#### 4. 请求日志中间件
```python
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response
```

#### 5. 集成第三方服务
```python
# 示例：集成Sentry
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[sentry_logging],
    traces_sample_rate=settings.telemetry_sample_rate
)
```

## 4. 邮件发送服务 (`email.py`)

### 功能
提供邮件发送功能，基于阿里云邮件推送服务。支持发送验证邮件、通知邮件等。

### 技术选型
- **服务商**: 阿里云邮件推送
- **免费额度**: 每天200封（需实名认证）
- **付费**: 超过后约 ¥0.01/封
- **优势**: 国内服务稳定、高送达率、数据合规

### 实现

```python
# app/core/email.py
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkdm.request.v20151123 import SingleSendMailRequest
from typing import Optional
from jinja2 import Template

from app.core.config import Settings


class EmailService:
    """基于阿里云邮件推送的邮件发送服务"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.aliyun_access_key_id = settings.aliyun_access_key_id
        self.aliyun_access_key_secret = settings.aliyun_access_key_secret
        self.aliyun_region = settings.aliyun_region
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        self.frontend_url = settings.frontend_url
        
        # 初始化阿里云客户端
        self.client = AcsClient(
            self.aliyun_access_key_id,
            self.aliyun_access_key_secret,
            self.aliyun_region
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选，阿里云主要使用HTML）
        
        Returns:
            bool: 是否发送成功
        """
        try:
            request = SingleSendMailRequest.SingleSendMailRequest()
            request.set_AccountName(self.from_email)  # 发信地址（需在阿里云控制台配置）
            request.set_FromAlias(self.from_name)      # 发信人昵称
            request.set_ToAddress(to_email)            # 收信地址
            request.set_Subject(subject)                # 邮件主题
            request.set_HtmlBody(html_content)          # 邮件正文（HTML格式）
            
            # 发送邮件
            response = self.client.do_action_with_exception(request)
            
            # 阿里云返回的是字节流，需要解码
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            
            # 检查响应（成功通常返回RequestId）
            return "RequestId" in response or True  # 根据实际响应调整
            
        except ClientException as e:
            # 客户端异常（如配置错误）
            print(f"Aliyun Client Error: {e.get_error_code()}, {e.get_error_msg()}")
            return False
        except ServerException as e:
            # 服务端异常
            print(f"Aliyun Server Error: {e.get_error_code()}, {e.get_error_msg()}")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_url: str,
        username: Optional[str] = None,
    ) -> bool:
        """发送邮箱验证邮件"""
        subject = "验证您的邮箱 - 工业问答系统"
        
        # HTML模板
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .button { display: inline-block; padding: 12px 24px; background-color: #007bff; 
                         color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
                .footer { margin-top: 30px; font-size: 12px; color: #666; text-align: center; }
                .url { word-break: break-all; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>欢迎注册工业问答系统</h2>
                </div>
                <div class="content">
                    <p>{% if username %}亲爱的 {{ username }}，{% endif %}</p>
                    <p>感谢您注册我们的服务。请点击以下按钮验证您的邮箱地址：</p>
                    <p style="text-align: center;">
                        <a href="{{ verification_url }}" class="button">验证邮箱</a>
                    </p>
                    <p>或者复制以下链接到浏览器中打开：</p>
                    <p class="url">{{ verification_url }}</p>
                    <p><strong>此链接将在24小时后过期。</strong></p>
                    <p>如果您没有注册此账户，请忽略此邮件。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>© 2025 Industrial QA System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 渲染模板
        html_content = Template(html_template).render(
            username=username,
            verification_url=verification_url
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        username: Optional[str] = None,
    ) -> bool:
        """发送密码重置邮件"""
        subject = "重置您的密码 - 工业问答系统"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .button { display: inline-block; padding: 12px 24px; background-color: #dc3545; 
                         color: white; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>密码重置请求</h2>
                <p>{% if username %}亲爱的 {{ username }}，{% endif %}</p>
                <p>您请求重置密码。请点击以下链接：</p>
                <p><a href="{{ reset_url }}" class="button">重置密码</a></p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
                <p>此链接将在1小时后过期。</p>
            </div>
        </body>
        </html>
        """
        
        html_content = Template(html_template).render(
            username=username,
            reset_url=reset_url
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )
```

### 使用方式

#### 依赖注入（推荐）
```python
# app/deps.py
from app.core.email import EmailService
from app.core.config import get_settings

def get_email_service(settings: Settings | None = None) -> EmailService:
    """获取邮件服务实例"""
    settings = settings or get_settings()
    return EmailService(settings)
```

#### 在API中使用
```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends
from app.core.email import EmailService
from app.deps import get_email_service

router = APIRouter(tags=["auth"])

@router.post("/send-verification-email")
async def send_verification_email(
    email: str,
    verification_url: str,
    email_service: EmailService = Depends(get_email_service),
):
    """发送验证邮件"""
    success = await email_service.send_verification_email(
        to_email=email,
        verification_url=verification_url,
    )
    
    if success:
        return {"message": "Verification email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")
```

### 阿里云邮件推送配置

#### 1. 开通服务
1. 登录阿里云控制台
2. 开通"邮件推送"服务
3. 完成实名认证（获取免费额度）

#### 2. 配置发信地址
1. 在邮件推送控制台添加发信地址
2. 验证域名或邮箱
3. 获取发信地址（用于 `FROM_EMAIL` 配置）

#### 3. 获取AccessKey
1. 在阿里云控制台创建AccessKey
2. 获取 AccessKey ID 和 AccessKey Secret
3. 配置到环境变量

### 费用说明

- **免费额度**: 每天200封（需实名认证）
- **超出费用**: 约 ¥0.01/封
- **适用场景**: 国内生产环境，中小到大规模应用

### 注意事项

1. **发信地址验证**: 必须在阿里云控制台配置并验证发信地址
2. **频率限制**: 注意发送频率限制，避免触发反垃圾邮件机制
3. **内容规范**: 邮件内容需符合规范，避免被标记为垃圾邮件
4. **错误处理**: 妥善处理发送失败的情况，记录日志并重试

## 模块间依赖关系

```
config.py
    ├─► security.py (Settings依赖)
    ├─► session.py (database_url配置)
    └─► 其他模块 (全局配置)

security.py
    └─► config.py (获取API token)

logging.py
    └─► (独立模块，在main.py中初始化)

email.py
    └─► config.py (获取邮件配置)
```

## 最佳实践

1. **配置管理**:
   - 敏感信息（API密钥）存储在环境变量中
   - 使用 `.env` 文件进行本地开发
   - 生产环境使用密钥管理服务（如AWS Secrets Manager）

2. **安全**:
   - 定期轮换API密钥
   - 使用HTTPS传输
   - 实施速率限制防止滥用

3. **日志**:
   - 记录关键操作和错误
   - 避免记录敏感信息（密码、令牌）
   - 使用结构化日志便于分析和查询

