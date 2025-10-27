from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ReportBase(BaseModel):
    name: str
    type: str
    filters: Optional[Dict[str, Any]] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class Report(ReportBase):
    id: int
    user_id: int
    data: Optional[Dict[str, Any]] = None
    status: str
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReportResponse(Report):
    pass

class AnalyticsBase(BaseModel):
    metric_name: str
    metric_value: float
    metric_type: str
    tags: Optional[Dict[str, Any]] = None

class AnalyticsCreate(AnalyticsBase):
    pass

class Analytics(AnalyticsBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class AnalyticsResponse(Analytics):
    pass

class CampaignReport(BaseModel):
    campaign_id: int
    campaign_name: str
    total_recipients: int
    sent_messages: int
    delivered_messages: int
    failed_messages: int
    delivery_rate: float
    cost: float
    created_at: datetime

class ContactReport(BaseModel):
    total_contacts: int
    active_contacts: int
    new_contacts_this_month: int
    contacts_by_group: Dict[str, int]

class MessageReport(BaseModel):
    total_messages: int
    sent_messages: int
    delivered_messages: int
    failed_messages: int
    messages_by_status: Dict[str, int]
    messages_by_day: List[Dict[str, Any]]

class BillingReport(BaseModel):
    total_spent: float
    total_recharged: float
    current_balance: float
    spending_by_month: List[Dict[str, Any]]
    transactions_count: int

class DashboardMetrics(BaseModel):
    campaigns: CampaignReport
    contacts: ContactReport
    messages: MessageReport
    billing: BillingReport
