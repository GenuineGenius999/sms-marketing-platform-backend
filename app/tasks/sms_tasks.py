from celery import Celery
from app.core.config import settings
from app.services.sms_service import process_campaign_messages
from app.database import SessionLocal

# Initialize Celery
celery_app = Celery(
    "sms_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def send_campaign_task(campaign_id: int):
    """
    Celery task to send campaign messages
    """
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(process_campaign_messages(campaign_id, db))
    finally:
        db.close()

@celery_app.task
def check_delivery_status_task():
    """
    Periodic task to check delivery status of sent messages
    """
    from app.models.message import Message, MessageStatus
    from app.services.sms_service import sms_service
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Get messages sent in the last 24 hours that are still pending delivery
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        messages = db.query(Message).filter(
            Message.status == MessageStatus.SENT,
            Message.sent_at >= cutoff_time
        ).all()
        
        for message in messages:
            if hasattr(message, 'vendor_message_id') and message.vendor_message_id:
                import asyncio
                result = asyncio.run(sms_service.check_delivery_status(message.vendor_message_id))
                
                if result.get("success") and result.get("status") == "delivered":
                    message.status = MessageStatus.DELIVERED
                    message.delivered_at = datetime.utcnow()
        
        db.commit()
    finally:
        db.close()

# Schedule periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'check-delivery-status': {
        'task': 'app.tasks.sms_tasks.check_delivery_status_task',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
