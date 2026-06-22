from pydantic import BaseModel, ConfigDict
from typing import Any, List


class Message(BaseModel):
    role: str
    content: Any
    model_config = ConfigDict(extra='allow')


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    model_config = ConfigDict(extra='allow')
