from pydantic import BaseModel, ConfigDict
from typing import Any


class Message(BaseModel):
    model_config = ConfigDict(extra='allow')
    role: str
    content: str | list[Any] | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra='allow')
    model: str
    messages: list[Message]
