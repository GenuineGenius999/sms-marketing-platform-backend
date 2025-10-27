from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.message import MessageStatus

class Message(BaseModel):
    id: int
    campaign_id: int
    recipient: str
    content: str
    status: MessageStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(Message):
    pass
