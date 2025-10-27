from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.models.message import Message, MessageStatus
from app.core.deps import get_current_active_user
from app.services.automation_service import AutomationService
from app.services.compliance_service import ComplianceService
from app.services.sms_service import sms_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/incoming")
async def handle_incoming_sms(request: Request, db: Session = Depends(get_db)):
    """Handle incoming SMS messages for two-way communication"""
    try:
        # Parse incoming webhook data
        data = await request.json()
        
        # Extract phone number and message
        phone = data.get("From", "").replace("+", "")
        message = data.get("Body", "")
        message_sid = data.get("MessageSid", "")
        
        logger.info(f"Received incoming SMS from {phone}: {message}")
        
        # Find contact by phone number
        contact = db.query(Contact).filter(Contact.phone == phone).first()
        
        if not contact:
            # Create new contact if not found
            contact = Contact(
                phone=phone,
                name=f"Contact {phone}",
                user_id=1,  # Default to admin user - in production, determine from phone
                is_active=True
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
        
        # Store incoming message
        incoming_message = Message(
            contact_id=contact.id,
            campaign_id=None,
            recipient=phone,
            content=message,
            status=MessageStatus.RECEIVED,
            sent_at=datetime.utcnow(),
            message_id=message_sid,
            is_incoming=True
        )
        db.add(incoming_message)
        db.commit()
        
        # Process automation triggers
        automation_service = AutomationService(db)
        automation_result = await automation_service.process_incoming_sms(
            phone=phone,
            message=message,
            user_id=contact.user_id
        )
        
        # Check compliance
        compliance_service = ComplianceService(db)
        compliance_status = compliance_service.get_contact_compliance_status(
            contact_id=contact.id,
            user_id=contact.user_id
        )
        
        # If contact has opted out, don't process further
        if not compliance_status.get("can_send", True):
            logger.info(f"Contact {phone} has opted out, not processing automation")
            return {"status": "opted_out", "message": "Contact has opted out"}
        
        # Process keyword triggers and automation
        if automation_result.get("success"):
            return {
                "status": "processed",
                "response": automation_result.get("response"),
                "automation_triggered": True
            }
        else:
            return {
                "status": "received",
                "message": "Message received but no automation triggered",
                "automation_triggered": False
            }
            
    except Exception as e:
        logger.error(f"Error handling incoming SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing incoming SMS"
        )

@router.post("/send-reply")
async def send_reply(
    contact_id: int,
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a reply to a contact"""
    try:
        # Get contact
        contact = db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        ).first()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Check compliance
        compliance_service = ComplianceService(db)
        compliance_status = compliance_service.get_contact_compliance_status(
            contact_id=contact_id,
            user_id=current_user.id
        )
        
        if not compliance_status.get("can_send", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact has opted out of receiving messages"
            )
        
        # Validate message compliance
        compliance_check = compliance_service.validate_message_compliance(
            message=message,
            user_id=current_user.id
        )
        
        if not compliance_check.get("is_compliant", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message compliance issues: {compliance_check.get('compliance_issues', [])}"
            )
        
        # Send SMS
        result = await sms_service.send_sms(
            phone=contact.phone,
            message=message,
            sender_id=None,
            campaign_id=None
        )
        
        if result.get("success"):
            # Store outgoing message
            outgoing_message = Message(
                contact_id=contact_id,
                campaign_id=None,
                recipient=contact.phone,
                content=message,
                status=MessageStatus.SENT,
                sent_at=datetime.utcnow(),
                message_id=result.get("message_id"),
                is_incoming=False
            )
            db.add(outgoing_message)
            db.commit()
            
            return {
                "success": True,
                "message": "Reply sent successfully",
                "message_id": result.get("message_id")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send reply: {result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending reply"
        )

@router.get("/conversations")
async def get_conversations(
    contact_id: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    try:
        query = db.query(Message).filter(Message.contact_id == contact_id)
        
        if contact_id:
            # Verify contact belongs to user
            contact = db.query(Contact).filter(
                Contact.id == contact_id,
                Contact.user_id == current_user.id
            ).first()
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Contact not found"
                )
        else:
            # Get all conversations for user
            query = query.join(Contact).filter(Contact.user_id == current_user.id)
        
        messages = query.order_by(Message.sent_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "contact_id": msg.contact_id,
                    "content": msg.content,
                    "status": msg.status.value,
                    "sent_at": msg.sent_at,
                    "is_incoming": msg.is_incoming,
                    "message_id": msg.message_id
                }
                for msg in messages
            ],
            "total": query.count()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting conversations"
        )

@router.post("/opt-out")
async def process_opt_out(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process an opt-out request"""
    try:
        # Get contact
        contact = db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        ).first()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Process opt-out
        compliance_service = ComplianceService(db)
        result = compliance_service.process_opt_out(
            contact_id=contact_id,
            user_id=current_user.id,
            opt_out_data={"method": "manual", "timestamp": datetime.utcnow().isoformat()}
        )
        
        if result.get("success"):
            return {"success": True, "message": "Contact opted out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing opt-out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing opt-out"
        )

@router.get("/opt-out-link/{token}")
async def process_unsubscribe_link(token: str, db: Session = Depends(get_db)):
    """Process unsubscribe link"""
    try:
        compliance_service = ComplianceService(db)
        result = compliance_service.process_unsubscribe_token(token)
        
        if result.get("success"):
            return {"success": True, "message": "Successfully unsubscribed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing unsubscribe link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing unsubscribe link"
        )
