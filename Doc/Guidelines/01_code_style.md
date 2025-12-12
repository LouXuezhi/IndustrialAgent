# 代码规范格式说明

> 创建时间: 2025-12-07  
> 适用范围: 工业问答后端项目所有Python代码

## 概述

本文档定义了工业问答后端项目的代码规范格式，包括命名规范、代码格式、类型提示、文档字符串等。所有代码应遵循本规范，以确保代码的可读性、可维护性和一致性。

## 1. 代码格式

### 1.1 行长度

- **最大行长度**: 100 字符
- **配置位置**: `pyproject.toml` 中的 `[tool.ruff]` 部分
- **规则**: 超过100字符的行应进行换行，遵循Python的换行规则

```python
# ✅ 正确：行长度在100字符以内
def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """根据邮箱查询用户"""
    pass

# ✅ 正确：长行进行换行
def create_document_library(
    session: AsyncSession,
    name: str,
    owner_id: UUID,
    owner_type: str,
    description: str | None = None
) -> DocumentLibrary:
    """创建文档库"""
    pass
```

### 1.2 缩进

- **缩进方式**: 使用4个空格，不使用Tab
- **续行缩进**: 与开括号对齐或使用悬挂缩进

```python
# ✅ 正确：与开括号对齐
result = await pipeline.run(
    query=query,
    top_k=top_k,
    library_ids=library_ids
)

# ✅ 正确：悬挂缩进
result = await pipeline.run(
    query=query,
    top_k=top_k,
    library_ids=library_ids
)
```

### 1.3 空行

- **模块级**: 顶层函数和类定义之间使用2个空行
- **类内**: 方法定义之间使用1个空行
- **函数内**: 逻辑块之间使用1个空行
- **导入**: 标准库、第三方库、本地模块之间使用1个空行

```python
# ✅ 正确：导入分组
import time
from typing import Any, Generic, TypeVar

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.response import StandardResponse
from app.agents.qa_agent import QAAgent


# ✅ 正确：类和函数之间2个空行
class AskRequest(BaseModel):
    query: str


class AskData(BaseModel):
    answer: str


def process_request(request: AskRequest) -> AskData:
    # 处理逻辑
    pass
```

### 1.4 引号

- **字符串引号**: 优先使用双引号 `"`，如果字符串内包含双引号则使用单引号 `'`
- **文档字符串**: 使用三引号 `"""`

```python
# ✅ 正确：使用双引号
message = "Hello, World!"

# ✅ 正确：字符串内包含双引号时使用单引号
message = 'He said "Hello"'

# ✅ 正确：文档字符串使用三引号
def my_function():
    """这是函数的文档字符串"""
    pass
```

## 2. 命名规范

### 2.1 变量和函数

- **变量名**: 使用小写字母，单词之间用下划线分隔（snake_case）
- **函数名**: 使用小写字母，单词之间用下划线分隔（snake_case）
- **常量**: 使用全大写字母，单词之间用下划线分隔（UPPER_CASE）

```python
# ✅ 正确：变量名
user_id = "123"
library_name = "My Library"
max_retry_count = 3

# ✅ 正确：函数名
def get_user_by_id(user_id: str) -> User:
    pass

async def send_verification_email(email: str) -> bool:
    pass

# ✅ 正确：常量
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

### 2.2 类名

- **类名**: 使用大驼峰命名（PascalCase）
- **异常类**: 以 `Error` 或 `Exception` 结尾

```python
# ✅ 正确：类名
class User(BaseModel):
    pass

class DocumentLibrary(Base):
    pass

class EmailService:
    pass

# ✅ 正确：异常类
class ValidationError(Exception):
    pass

class DatabaseConnectionError(Exception):
    pass
```

### 2.3 私有成员

- **私有属性/方法**: 使用单下划线前缀 `_`
- **名称修饰**: 仅在必要时使用双下划线前缀 `__`（避免与Python内部名称冲突）

```python
# ✅ 正确：私有属性
class EmailService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = self._create_client()
    
    def _create_client(self):
        """私有方法"""
        pass
```

### 2.4 模块和包

- **模块名**: 使用小写字母，单词之间用下划线分隔（snake_case）
- **包名**: 使用小写字母，单词之间用下划线分隔（snake_case）

```python
# ✅ 正确：模块名
# app/core/email.py
# app/users/auth.py
# app/rag/pipeline.py
```

## 3. 类型提示

### 3.1 基本要求

- **所有函数**: 必须包含类型提示（参数和返回值）
- **类属性**: 使用类型注解
- **类型导入**: 从 `typing` 模块导入类型

```python
# ✅ 正确：完整的类型提示
from typing import Any, Optional

def get_user_by_id(user_id: str) -> Optional[User]:
    """根据ID查询用户"""
    pass

async def process_data(
    data: list[dict[str, Any]],
    timeout: int = 30
) -> dict[str, Any]:
    """处理数据"""
    pass
```

### 3.2 常用类型

```python
# ✅ 基本类型
name: str
age: int
price: float
is_active: bool

# ✅ 集合类型
items: list[str]
scores: dict[str, int]
tags: set[str]

# ✅ 可选类型
email: str | None  # Python 3.10+
email: Optional[str]  # Python < 3.10

# ✅ 联合类型
id: str | int
result: User | None

# ✅ 泛型
from typing import Generic, TypeVar

T = TypeVar("T")

class Response(Generic[T]):
    data: T
```

### 3.3 异步函数

```python
# ✅ 正确：异步函数类型提示
async def fetch_data(url: str) -> dict[str, Any]:
    """异步获取数据"""
    pass

async def process_items(items: list[str]) -> list[dict]:
    """异步处理项目列表"""
    pass
```

## 4. 文档字符串（Docstring）

### 4.1 基本格式

- **格式**: 使用三引号 `"""`
- **风格**: Google风格或NumPy风格
- **位置**: 紧跟在函数/类定义之后

```python
# ✅ 正确：Google风格
def get_user_by_id(user_id: str) -> User | None:
    """根据用户ID查询用户
    
    Args:
        user_id: 用户唯一标识符
        
    Returns:
        用户对象，如果不存在则返回None
        
    Raises:
        ValueError: 当user_id格式无效时
    """
    pass

# ✅ 正确：简洁风格（简单函数）
def calculate_total(items: list[float]) -> float:
    """计算项目列表的总和"""
    return sum(items)
```

### 4.2 类文档字符串

```python
# ✅ 正确：类文档字符串
class EmailService:
    """基于阿里云邮件推送的邮件发送服务
    
    提供发送验证邮件、通知邮件等功能。
    使用阿里云邮件推送服务，支持HTML格式邮件。
    
    Attributes:
        settings: 应用配置对象
        client: 阿里云客户端实例
    """
    
    def __init__(self, settings: Settings):
        """初始化邮件服务
        
        Args:
            settings: 应用配置对象，包含阿里云相关配置
        """
        self.settings = settings
```

### 4.3 模块文档字符串

```python
# ✅ 正确：模块文档字符串（文件顶部）
"""邮件发送服务模块

提供基于阿里云邮件推送的邮件发送功能。
支持发送验证邮件、密码重置邮件等。
"""

from app.core.config import Settings
```

## 5. 导入规范

### 5.1 导入顺序

1. **标准库导入**
2. **第三方库导入**
3. **本地模块导入**

每组之间使用1个空行分隔。

```python
# ✅ 正确：导入顺序
import time
from typing import Any, Optional
from functools import lru_cache

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.email import EmailService
from app.db.models import User
```

### 5.2 导入方式

- **绝对导入**: 优先使用绝对导入
- **相对导入**: 仅在包内部使用相对导入
- **导入别名**: 仅在必要时使用别名

```python
# ✅ 正确：绝对导入
from app.core.config import Settings
from app.db.models import User

# ✅ 正确：相对导入（仅在包内部）
from .models import User
from ..core.config import Settings

# ✅ 正确：导入别名
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession
```

## 6. 异常处理

### 6.1 异常捕获

- **具体异常**: 捕获具体的异常类型，避免使用裸露的 `except:`
- **异常信息**: 记录详细的异常信息
- **重新抛出**: 必要时重新抛出异常或转换为业务异常

```python
# ✅ 正确：捕获具体异常
try:
    result = await database.query(sql)
except DatabaseError as e:
    logger.error(f"Database query failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise ValueError("Operation failed") from e

# ❌ 错误：捕获所有异常
try:
    result = await database.query(sql)
except:  # 不要这样做
    pass
```

### 6.2 自定义异常

```python
# ✅ 正确：自定义异常
class ValidationError(Exception):
    """数据验证错误"""
    pass

class EmailSendError(Exception):
    """邮件发送错误"""
    pass

# 使用
if not email:
    raise ValidationError("Email is required")
```

## 7. 异步编程规范

### 7.1 异步函数

- **异步I/O操作**: 必须使用 `async/await`
- **数据库操作**: 使用异步数据库会话
- **HTTP请求**: 使用异步HTTP客户端

```python
# ✅ 正确：异步函数
async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """异步查询用户"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# ✅ 正确：异步HTTP请求
async def fetch_external_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### 7.2 上下文管理器

```python
# ✅ 正确：异步上下文管理器
async def process_with_session():
    async with async_session() as session:
        user = await get_user_by_id(session, user_id)
        await session.commit()
```

## 8. 代码组织

### 8.1 文件结构

```python
# ✅ 正确：文件结构顺序
"""
模块文档字符串
"""

# 1. 标准库导入
import time
from typing import Any

# 2. 第三方库导入
from fastapi import APIRouter
from pydantic import BaseModel

# 3. 本地模块导入
from app.core.config import Settings

# 4. 常量定义
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 5. 类型定义
T = TypeVar("T")

# 6. 类定义
class MyClass:
    """类文档字符串"""
    pass

# 7. 函数定义
def my_function():
    """函数文档字符串"""
    pass

# 8. 模块级代码（如果必要）
if __name__ == "__main__":
    pass
```

### 8.2 函数长度

- **建议**: 单个函数不超过50行
- **过长函数**: 拆分为多个小函数

```python
# ✅ 正确：短函数
def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# ✅ 正确：长函数拆分为多个函数
def process_user_registration(data: dict) -> User:
    """处理用户注册"""
    validate_registration_data(data)
    user = create_user(data)
    send_verification_email(user)
    return user

def validate_registration_data(data: dict) -> None:
    """验证注册数据"""
    # 验证逻辑
    pass

def create_user(data: dict) -> User:
    """创建用户"""
    # 创建逻辑
    pass
```

## 9. 注释规范

### 9.1 代码注释

- **行内注释**: 使用 `#`，与代码之间至少2个空格
- **块注释**: 使用 `#`，每行一个注释
- **TODO注释**: 使用 `# TODO: 描述`

```python
# ✅ 正确：行内注释
result = calculate_total(items)  # 计算总和

# ✅ 正确：块注释
# 这里需要处理特殊情况：
# 1. 空列表
# 2. 负数
# 3. 溢出

# ✅ 正确：TODO注释
# TODO: 添加缓存机制以提高性能
def expensive_operation():
    pass
```

### 9.2 避免不必要的注释

```python
# ❌ 错误：不必要的注释
# 设置变量x为10
x = 10

# ✅ 正确：代码自解释
total_count = 10
```

## 10. 测试代码规范

### 10.1 测试文件命名

- **测试文件**: 以 `test_` 开头
- **测试函数**: 以 `test_` 开头

```python
# ✅ 正确：测试文件
# tests/test_user_management.py
# tests/test_email_service.py

# ✅ 正确：测试函数
def test_get_user_by_id():
    """测试根据ID查询用户"""
    pass

async def test_send_verification_email():
    """测试发送验证邮件"""
    pass
```

### 10.2 测试结构

```python
# ✅ 正确：测试结构
import pytest
from app.core.email import EmailService

class TestEmailService:
    """邮件服务测试类"""
    
    async def test_send_email_success(self):
        """测试成功发送邮件"""
        # Arrange
        service = EmailService(settings)
        
        # Act
        result = await service.send_email(...)
        
        # Assert
        assert result is True
```

## 11. 配置和常量

### 11.1 配置管理

- **使用Pydantic Settings**: 统一管理配置
- **环境变量**: 敏感信息使用环境变量
- **默认值**: 提供合理的默认值

```python
# ✅ 正确：使用Pydantic Settings
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    app_name: str = Field(default="Industrial QA Backend")
    database_url: str = Field(default="sqlite:///./app.db")
    
    class Config:
        env_file = ".env"
```

### 11.2 常量定义

```python
# ✅ 正确：常量定义
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
```

## 12. 最佳实践

### 12.1 代码可读性

- **有意义的变量名**: 使用描述性的变量名
- **避免魔法数字**: 使用常量替代
- **单一职责**: 每个函数只做一件事

```python
# ❌ 错误：魔法数字
if retry_count > 3:
    raise Error()

# ✅ 正确：使用常量
MAX_RETRY_COUNT = 3
if retry_count > MAX_RETRY_COUNT:
    raise Error()
```

### 12.2 性能优化

- **异步I/O**: 使用异步操作提高性能
- **数据库查询**: 避免N+1查询问题
- **缓存**: 合理使用缓存

```python
# ✅ 正确：批量查询
users = await session.execute(
    select(User).where(User.id.in_(user_ids))
).scalars().all()
```

### 12.3 安全性

- **输入验证**: 验证所有用户输入
- **敏感信息**: 不在代码中硬编码敏感信息
- **SQL注入**: 使用参数化查询

```python
# ✅ 正确：参数化查询
result = await session.execute(
    select(User).where(User.email == email)
)
```

## 13. 参考资源

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## 14. 检查工具

项目使用以下工具自动检查和格式化代码：

- **Ruff**: 代码格式化和静态检查
- **配置**: `pyproject.toml` 中的 `[tool.ruff]` 部分

详细说明请参考 [代码检测说明](./02_code_checking.md)。



