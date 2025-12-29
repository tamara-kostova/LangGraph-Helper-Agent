import os

from fastapi import APIRouter, Depends

from api.deps import get_helper_agent
from api.models import ChatRequest, ChatResponse
from app.agent import HelperAgent

AGENT_MODE = os.getenv("AGENT_MODE", "local")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    agent: HelperAgent = Depends(get_helper_agent),
):
    result = await agent.achat(
        messages=[m.model_dump() for m in req.messages],
        thread_id=req.thread_id or "default",
    )
    return ChatResponse(**result)
