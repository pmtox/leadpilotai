from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class MessageBase(BaseModel):
    speaker: str
    content: str
    language: Optional[str] = "English"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationStartRequest(BaseModel):
    customer_id: int
    initial_language: Optional[str] = "English"

class MessageTurnRequest(BaseModel):
    message: str
    language: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration: int
    summary: Optional[str] = None
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)
