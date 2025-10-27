from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.campaign import Campaign
from app.schemas.message import MessageResponse
from app.core.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=list[MessageResponse])
async def read_messages(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    messages = db.query(Message).join(Campaign).filter(
        Campaign.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return messages

@router.get("/{message_id}", response_model=MessageResponse)
async def read_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    message = db.query(Message).join(Campaign).filter(
        Message.id == message_id,
        Campaign.user_id == current_user.id
    ).first()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
