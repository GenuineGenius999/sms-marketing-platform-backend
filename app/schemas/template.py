from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SmsTemplateBase(BaseModel):
    name: str
    content: str

class SmsTemplateCreate(SmsTemplateBase):
    pass

class SmsTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

class SmsTemplate(SmsTemplateBase):
    id: int
    user_id: int
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
