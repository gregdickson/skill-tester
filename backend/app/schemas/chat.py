from pydantic import BaseModel


class ChatRequest(BaseModel):
    mode: str  # "learn" or "command"
    message: str


class ChatResponse(BaseModel):
    message: str
    config_changed: bool = False
    action_triggered: str | None = None
