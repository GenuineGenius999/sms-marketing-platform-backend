from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.template import SmsTemplate
from app.models.sender_id import SenderId
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.message import Message, MessageStatus
from app.schemas.template import SmsTemplate as SmsTemplateSchema
from app.schemas.sender_id import SenderId as SenderIdSchema, SenderIdCreate, SenderIdUpdate
from app.schemas.dashboard import AdminDashboardStats
from app.schemas.user import UserResponse, UserUpdate
from app.core.deps import get_admin_user

router = APIRouter()

# Admin Dashboard Stats
@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_admin_dashboard_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Get total users
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Get total campaigns
    total_campaigns = db.query(Campaign).count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == CampaignStatus.SENDING).count()
    
    # Get total contacts
    total_contacts = db.query(Contact).count()
    
    # Get total messages sent
    total_messages = db.query(Message).count()
    sent_messages = db.query(Message).filter(Message.status == MessageStatus.SENT).count()
    failed_messages = db.query(Message).filter(Message.status == MessageStatus.FAILED).count()
    
    # Get total templates
    total_templates = db.query(SmsTemplate).count()
    approved_templates = db.query(SmsTemplate).filter(SmsTemplate.is_approved == True).count()
    
    # Get total sender IDs
    total_sender_ids = db.query(SenderId).count()
    approved_sender_ids = db.query(SenderId).filter(SenderId.is_approved == True).count()
    
    # Calculate revenue (assuming $0.01 per message)
    revenue = sent_messages * 0.01
    
    return AdminDashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_contacts=total_contacts,
        total_messages=total_messages,
        sent_messages=sent_messages,
        failed_messages=failed_messages,
        total_templates=total_templates,
        approved_templates=approved_templates,
        total_sender_ids=total_sender_ids,
        approved_sender_ids=approved_sender_ids,
        revenue=revenue
    )

# Template approval endpoints
@router.get("/templates", response_model=list[SmsTemplateSchema])
async def read_all_templates(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    templates = db.query(SmsTemplate).offset(skip).limit(limit).all()
    return templates

@router.put("/templates/{template_id}/approve")
async def approve_template(
    template_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    template = db.query(SmsTemplate).filter(SmsTemplate.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_approved = True
    db.commit()
    return {"message": "Template approved successfully"}

@router.put("/templates/{template_id}/reject")
async def reject_template(
    template_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    template = db.query(SmsTemplate).filter(SmsTemplate.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_approved = False
    db.commit()
    return {"message": "Template rejected"}

# Sender ID management endpoints
@router.get("/sender-ids", response_model=list[SenderIdSchema])
async def read_sender_ids(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    sender_ids = db.query(SenderId).all()
    return sender_ids

@router.post("/sender-ids", response_model=SenderIdSchema)
async def create_sender_id(
    sender_id: SenderIdCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    db_sender_id = SenderId(
        sender_id=sender_id.sender_id,
        user_id=admin_user.id,  # For now, assign to admin
        is_approved=True
    )
    db.add(db_sender_id)
    db.commit()
    db.refresh(db_sender_id)
    return db_sender_id

@router.put("/sender-ids/{sender_id_id}/approve")
async def approve_sender_id(
    sender_id_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    sender_id = db.query(SenderId).filter(SenderId.id == sender_id_id).first()
    if sender_id is None:
        raise HTTPException(status_code=404, detail="Sender ID not found")
    
    sender_id.is_approved = True
    db.commit()
    return {"message": "Sender ID approved successfully"}

@router.put("/sender-ids/{sender_id_id}/reject")
async def reject_sender_id(
    sender_id_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    sender_id = db.query(SenderId).filter(SenderId.id == sender_id_id).first()
    if sender_id is None:
        raise HTTPException(status_code=404, detail="Sender ID not found")
    
    sender_id.is_approved = False
    db.commit()
    return {"message": "Sender ID rejected"}

# Campaign management endpoints
@router.get("/campaigns", response_model=list[dict])
async def read_all_campaigns(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns across all users for admin"""
    campaigns = db.query(Campaign).offset(skip).limit(limit).all()
    campaign_data = []
    for campaign in campaigns:
        user = db.query(User).filter(User.id == campaign.user_id).first()
        campaign_data.append({
            "id": campaign.id,
            "name": campaign.name,
            "message": campaign.message,
            "user_id": campaign.user_id,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "unknown@example.com",
            "status": campaign.status.value,
            "scheduled_at": campaign.scheduled_at,
            "sent_at": campaign.sent_at,
            "total_recipients": campaign.total_recipients,
            "delivered_count": campaign.delivered_count,
            "failed_count": campaign.failed_count,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at
        })
    return campaign_data

# User management endpoints
@router.get("/users", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Vendor management endpoints
@router.get("/vendors", response_model=list[dict])
async def read_vendors(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get SMS vendors configuration"""
    # Mock data for now - in real app this would be from a vendors table
    vendors = [
        {
            "id": 1,
            "name": "Twilio SMS",
            "provider": "twilio",
            "api_key": "AC****1234",
            "api_secret": "****",
            "webhook_url": "https://api.twilio.com/webhooks",
            "is_active": True,
            "cost_per_sms": 0.0075,
            "currency": "USD",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "name": "AWS SNS",
            "provider": "aws_sns",
            "api_key": "AKIA****",
            "api_secret": "****",
            "webhook_url": "https://sns.amazonaws.com/webhooks",
            "is_active": True,
            "cost_per_sms": 0.00645,
            "currency": "USD",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 3,
            "name": "Vonage SMS",
            "provider": "vonage",
            "api_key": "VONAGE****",
            "api_secret": "****",
            "webhook_url": "https://api.nexmo.com/webhooks",
            "is_active": False,
            "cost_per_sms": 0.005,
            "currency": "USD",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
    return vendors

# Reports endpoints
@router.get("/reports", response_model=dict)
async def get_admin_reports(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive platform reports"""
    # Get platform-wide statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_campaigns = db.query(Campaign).count()
    total_messages = db.query(Message).count()
    sent_messages = db.query(Message).filter(Message.status == MessageStatus.SENT).count()
    failed_messages = db.query(Message).filter(Message.status == MessageStatus.FAILED).count()
    
    # Calculate success rate
    success_rate = (sent_messages / total_messages * 100) if total_messages > 0 else 0
    
    # Calculate revenue (assuming $0.01 per message)
    revenue = sent_messages * 0.01
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_campaigns": total_campaigns,
        "total_messages": total_messages,
        "sent_messages": sent_messages,
        "failed_messages": failed_messages,
        "success_rate": round(success_rate, 2),
        "revenue": round(revenue, 2),
        "top_campaigns": [],
        "top_users": [],
        "daily_stats": []
    }
