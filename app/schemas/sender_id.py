from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SenderIdBase(BaseModel):
    sender_id: str

class SenderIdCreate(SenderIdBase):
    pass

class SenderIdUpdate(BaseModel):
    sender_id: Optional[str] = None

class SenderId(SenderIdBase):
    id: int
    user_id: int
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
