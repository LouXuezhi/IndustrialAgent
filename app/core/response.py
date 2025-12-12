"""统一响应格式工具"""
import time
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式"""
    code: int = 0
    message: str = "success"
    data: T
    timestamp: int | None = None

    def __init__(self, data: T, code: int = 0, message: str = "success", **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = int(time.time())
        super().__init__(code=code, message=message, data=data, **kwargs)


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    detail: str | None = None

