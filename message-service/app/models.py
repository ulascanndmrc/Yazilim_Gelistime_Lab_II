from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    content: str
    recipient_id: Optional[str] = None
    channel: str = "general"


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    channel: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    content: str
    sender_id: str
    recipient_id: Optional[str]
    channel: str
    created_at: datetime
    updated_at: Optional[datetime] = None
