from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.campaign import Campaign
from app.models.message import Message, MessageStatus
from app.models.contact import Contact, ContactGroup
from app.schemas.dashboard import DashboardStats
from app.core.deps import get_current_active_user

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get campaign stats
    total_campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).count()
    
    # Get message stats
    total_messages = db.query(Message).join(Campaign).filter(Campaign.user_id == current_user.id).count()
    delivered_messages = db.query(Message).join(Campaign).filter(
        Campaign.user_id == current_user.id,
        Message.status == MessageStatus.DELIVERED
    ).count()
    failed_messages = db.query(Message).join(Campaign).filter(
        Campaign.user_id == current_user.id,
        Message.status == MessageStatus.FAILED
    ).count()
    pending_messages = db.query(Message).join(Campaign).filter(
        Campaign.user_id == current_user.id,
        Message.status == MessageStatus.PENDING
    ).count()
    
    # Get contact stats
    total_contacts = db.query(Contact).filter(Contact.user_id == current_user.id).count()
    total_groups = db.query(ContactGroup).filter(ContactGroup.user_id == current_user.id).count()
    
    return DashboardStats(
        total_campaigns=total_campaigns,
        total_messages=total_messages,
        delivered_messages=delivered_messages,
        failed_messages=failed_messages,
        pending_messages=pending_messages,
        total_contacts=total_contacts,
        total_groups=total_groups,
        balance=current_user.balance
    )
