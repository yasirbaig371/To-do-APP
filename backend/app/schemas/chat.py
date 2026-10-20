from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)
    confirm: bool | None = None


class ChatResponse(BaseModel):
    response: str
    requires_confirmation: bool = False
    tool_name: str | None = None
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
