from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agents.qa_agent import QAAgent
from app.core.security import get_api_key
from app.deps import get_pipeline
from app.rag.pipeline import RAGPipeline


class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, description="User's natural language question")
    tenant_id: str | None = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    references: list[dict] = Field(default_factory=list)
    latency_ms: int


router = APIRouter(tags=["qa"])


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(get_api_key)])
async def ask_entrypoint(
    payload: AskRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> AskResponse:
    agent = QAAgent(pipeline=pipeline)
    result = await agent.run(query=payload.query, top_k=payload.top_k, tenant_id=payload.tenant_id)
    return AskResponse(**result)

