from typing import List, Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    thread_id: str | None = "default"


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["offline", "online"]
    sources: list
