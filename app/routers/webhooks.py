from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.message import Message, MessageStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/delivery-report")
async def handle_delivery_report(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle delivery reports from SMS providers"""
    try:
        # Get the raw request body
        body = await request.body()
        
        # Parse the webhook data (this would be provider-specific)
        # For now, we'll handle a generic format
        import json
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            # If not JSON, try form data
            form_data = await request.form()
            data = dict(form_data)
        
        # Extract message ID and status
        message_id = data.get('message_id') or data.get('sid') or data.get('id')
        status = data.get('status') or data.get('delivery_status')
        
        if not message_id or not status:
            logger.warning(f"Invalid webhook data: {data}")
            return {"status": "error", "message": "Missing required fields"}
        
        # Map provider status to our internal status
        status_mapping = {
            'delivered': MessageStatus.SENT,
            'sent': MessageStatus.SENT,
            'failed': MessageStatus.FAILED,
            'undelivered': MessageStatus.FAILED,
            'pending': MessageStatus.PENDING,
            'queued': MessageStatus.PENDING
        }
        
        internal_status = status_mapping.get(status.lower(), MessageStatus.PENDING)
        
        # Find the message in our database
        message = db.query(Message).filter(
            Message.provider_message_id == message_id
        ).first()
        
        if not message:
            logger.warning(f"Message not found for ID: {message_id}")
            return {"status": "error", "message": "Message not found"}
        
        # Update message status
        message.status = internal_status
        message.delivered_at = datetime.utcnow() if internal_status == MessageStatus.SENT else None
        message.error_message = data.get('error_message') if internal_status == MessageStatus.FAILED else None
        
        db.commit()
        
        # Update campaign statistics
        campaign = db.query(Campaign).filter(Campaign.id == message.campaign_id).first()
        if campaign:
            # Recalculate campaign stats
            sent_count = db.query(Message).filter(
                Message.campaign_id == campaign.id,
                Message.status == MessageStatus.SENT
            ).count()
            
            failed_count = db.query(Message).filter(
                Message.campaign_id == campaign.id,
                Message.status == MessageStatus.FAILED
            ).count()
            
            campaign.delivered_count = sent_count
            campaign.failed_count = failed_count
            
            # Check if campaign is complete
            total_messages = db.query(Message).filter(
                Message.campaign_id == campaign.id
            ).count()
            
            if sent_count + failed_count >= total_messages:
                campaign.status = CampaignStatus.SENT
                campaign.sent_at = datetime.utcnow()
            
            db.commit()
        
        logger.info(f"Updated message {message_id} status to {internal_status}")
        return {"status": "success", "message": "Status updated"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": "Internal server error"}

@router.post("/twilio")
async def handle_twilio_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Twilio-specific webhooks"""
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        message_sid = data.get('MessageSid')
        message_status = data.get('MessageStatus')
        
        if not message_sid or not message_status:
            return {"status": "error"}
        
        # Find message by Twilio SID
        message = db.query(Message).filter(
            Message.provider_message_id == message_sid
        ).first()
        
        if message:
            # Map Twilio status to our status
            status_mapping = {
                'delivered': MessageStatus.SENT,
                'sent': MessageStatus.SENT,
                'failed': MessageStatus.FAILED,
                'undelivered': MessageStatus.FAILED,
                'pending': MessageStatus.PENDING,
                'queued': MessageStatus.PENDING
            }
            
            internal_status = status_mapping.get(message_status.lower(), MessageStatus.PENDING)
            message.status = internal_status
            
            if internal_status == MessageStatus.SENT:
                message.delivered_at = datetime.utcnow()
            elif internal_status == MessageStatus.FAILED:
                message.error_message = data.get('ErrorMessage', 'Delivery failed')
            
            db.commit()
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Twilio webhook error: {str(e)}")
        return {"status": "error"}

@router.post("/aws-sns")
async def handle_aws_sns_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle AWS SNS webhooks"""
    try:
        body = await request.body()
        import json
        data = json.loads(body.decode('utf-8'))
        
        # AWS SNS webhook processing would go here
        # This is a simplified version
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"AWS SNS webhook error: {str(e)}")
        return {"status": "error"}

@router.post("/vonage")
async def handle_vonage_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Vonage (Nexmo) webhooks"""
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        # Vonage webhook processing would go here
        # This is a simplified version
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Vonage webhook error: {str(e)}")
        return {"status": "error"}
