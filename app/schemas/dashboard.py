from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_campaigns: int
    total_messages: int
    delivered_messages: int
    failed_messages: int
    pending_messages: int
    total_contacts: int
    total_groups: int
    balance: float

class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_campaigns: int
    active_campaigns: int
    total_contacts: int
    total_messages: int
    sent_messages: int
    failed_messages: int
    total_templates: int
    approved_templates: int
    total_sender_ids: int
    approved_sender_ids: int
    revenue: float
