from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.message import Message, MessageStatus
from app.schemas.campaign import Campaign as CampaignSchema, CampaignCreate, CampaignUpdate, CampaignResponse
from app.core.deps import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=list[CampaignResponse])
async def read_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).offset(skip).limit(limit).all()
    return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_campaign = Campaign(
        name=campaign.name,
        message=campaign.message,
        template_id=campaign.template_id,
        user_id=current_user.id,
        scheduled_at=campaign.scheduled_at
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def read_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for field, value in campaign_update.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    return campaign

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted successfully"}

@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    contact_ids: list[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get contacts
    contacts = db.query(Contact).filter(
        Contact.id.in_(contact_ids),
        Contact.user_id == current_user.id
    ).all()
    
    if not contacts:
        raise HTTPException(status_code=400, detail="No valid contacts found")
    
    # Update campaign status
    campaign.status = CampaignStatus.SENDING
    campaign.total_recipients = len(contacts)
    campaign.sent_at = datetime.utcnow()
    
    # Create messages
    for contact in contacts:
        message = Message(
            campaign_id=campaign.id,
            recipient=contact.phone,
            content=campaign.message,
            status=MessageStatus.PENDING
        )
        db.add(message)
    
    db.commit()
    return {"message": f"Campaign sent to {len(contacts)} contacts"}

@router.get("/{campaign_id}/messages")
async def get_campaign_messages(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    messages = db.query(Message).filter(Message.campaign_id == campaign_id).all()
    return messages
