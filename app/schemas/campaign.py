from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.campaign import CampaignStatus

class CampaignBase(BaseModel):
    name: str
    message: str

class CampaignCreate(CampaignBase):
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    message: Optional[str] = None
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None

class Campaign(CampaignBase):
    id: int
    user_id: int
    template_id: Optional[int] = None
    status: CampaignStatus
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    total_recipients: int
    delivered_count: int
    failed_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CampaignResponse(Campaign):
    pass
