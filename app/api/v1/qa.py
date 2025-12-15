from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agents.qa_agent import QAAgent
from app.core.response import StandardResponse
from app.core.security import get_current_user
from app.db.models import User
from app.deps import get_pipeline
from app.rag.pipeline import RAGPipeline


class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, description="User's natural language question")
    library_ids: list[str] | None = Field(
        default=None,
        description="指定的文档库ID列表，不指定则搜索所有可访问的文档库"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="返回的检索结果数量")


class AskData(BaseModel):
    """问答响应数据"""
    answer: str
    references: list[dict] = Field(default_factory=list)
    latency_ms: int


router = APIRouter(tags=["qa"])


@router.post("/ask")
async def ask_entrypoint(
    payload: AskRequest,
    pipeline: Annotated[RAGPipeline, Depends(get_pipeline)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StandardResponse[AskData]:
    agent = QAAgent(pipeline=pipeline)
    result = await agent.run(
        query=payload.query,
        top_k=payload.top_k,
        library_ids=payload.library_ids,
        role=current_user.role,  # 传递用户角色，用于选择对应的 prompt
    )
    return StandardResponse(data=AskData(**result))

