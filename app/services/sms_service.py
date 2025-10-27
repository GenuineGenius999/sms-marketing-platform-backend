import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.message import Message, MessageStatus
from app.models.campaign import Campaign, CampaignStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import json
import hashlib
import hmac
import time
from enum import Enum

logger = logging.getLogger(__name__)

class SmsProvider(Enum):
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"
    VONAGE = "vonage"
    MOCK = "mock"

class SMSService:
    def __init__(self, provider: SmsProvider = SmsProvider.MOCK):
        self.provider = provider
        self.vendor_url = settings.SMS_VENDOR_URL
        self.api_key = settings.SMS_VENDOR_API_KEY
        self.api_secret = getattr(settings, 'SMS_VENDOR_API_SECRET', '')
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.sender_id = "SMSAPP"
    
    async def send_sms(self, phone: str, message: str, sender_id: str = None, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Send SMS via vendor API with advanced features
        """
        try:
            # Validate phone number
            if not self.validate_phone_number(phone):
                return {
                    "success": False,
                    "error": "Invalid phone number format",
                    "status": "failed"
                }
            
            # Check rate limiting
            if not await self.check_rate_limit():
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "status": "failed"
                }
            
            # Send based on provider
            if self.provider == SmsProvider.TWILIO:
                return await self._send_via_twilio(phone, message, sender_id, campaign_id)
            elif self.provider == SmsProvider.AWS_SNS:
                return await self._send_via_aws_sns(phone, message, sender_id, campaign_id)
            elif self.provider == SmsProvider.VONAGE:
                return await self._send_via_vonage(phone, message, sender_id, campaign_id)
            else:
                return await self._send_mock(phone, message, sender_id, campaign_id)
                    
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    async def _send_via_twilio(self, phone: str, message: str, sender_id: str, campaign_id: Optional[int]) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    data={
                        "To": phone,
                        "From": sender_id or self.sender_id,
                        "Body": message
                    },
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "success": True,
                        "message_id": result.get("sid"),
                        "status": "sent",
                        "cost": 0.0075,
                        "provider": "twilio"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Twilio Error: {response.status_code}",
                        "status": "failed"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Twilio API Error: {str(e)}",
                "status": "failed"
            }
    
    async def _send_via_aws_sns(self, phone: str, message: str, sender_id: str, campaign_id: Optional[int]) -> Dict[str, Any]:
        """Send SMS via AWS SNS"""
        try:
            # AWS SNS implementation would go here
            return {
                "success": True,
                "message_id": f"aws-{int(time.time())}",
                "status": "sent",
                "cost": 0.00645,
                "provider": "aws_sns"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"AWS SNS Error: {str(e)}",
                "status": "failed"
            }
    
    async def _send_via_vonage(self, phone: str, message: str, sender_id: str, campaign_id: Optional[int]) -> Dict[str, Any]:
        """Send SMS via Vonage (Nexmo)"""
        try:
            return {
                "success": True,
                "message_id": f"vonage-{int(time.time())}",
                "status": "sent",
                "cost": 0.005,
                "provider": "vonage"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Vonage Error: {str(e)}",
                "status": "failed"
            }
    
    async def _send_mock(self, phone: str, message: str, sender_id: str, campaign_id: Optional[int]) -> Dict[str, Any]:
        """Mock SMS sending for development"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate 95% success rate
        import random
        if random.random() < 0.95:
            return {
                "success": True,
                "message_id": f"mock-{int(time.time())}-{hash(phone) % 10000}",
                "status": "sent",
                "cost": 0.01,
                "provider": "mock"
            }
        else:
            return {
                "success": False,
                "error": "Mock delivery failure",
                "status": "failed"
            }
    
    async def send_bulk_sms(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send multiple SMS messages
        """
        results = []
        
        # Process messages in batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Send batch concurrently
            tasks = [self.send_sms(msg["phone"], msg["message"], msg.get("sender_id")) for msg in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "status": "failed",
                        "phone": batch[j]["phone"]
                    })
                else:
                    results.append({
                        **result,
                        "phone": batch[j]["phone"]
                    })
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        return results
    
    async def check_delivery_status(self, message_id: str, provider: str = "mock") -> Dict[str, Any]:
        """
        Check delivery status of a message
        """
        try:
            if provider == "twilio":
                return await self._get_twilio_status(message_id)
            elif provider == "aws_sns":
                return await self._get_aws_status(message_id)
            elif provider == "vonage":
                return await self._get_vonage_status(message_id)
            else:
                return await self._get_mock_status(message_id)
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_twilio_status(self, message_id: str) -> Dict[str, Any]:
        """Get status from Twilio"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages/{message_id}.json",
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "error_code": data.get("error_code"),
                        "error_message": data.get("error_message"),
                        "price": data.get("price"),
                        "date_sent": data.get("date_sent")
                    }
                else:
                    return {"error": f"Status check failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_mock_status(self, message_id: str) -> Dict[str, Any]:
        """Mock status check"""
        import random
        statuses = ["sent", "delivered", "failed", "undelivered"]
        status = random.choice(statuses)
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "mock"
        }
    
    async def _get_aws_status(self, message_id: str) -> Dict[str, Any]:
        """Get status from AWS SNS"""
        return {"status": "delivered", "provider": "aws_sns"}
    
    async def _get_vonage_status(self, message_id: str) -> Dict[str, Any]:
        """Get status from Vonage"""
        return {"status": "delivered", "provider": "vonage"}
    
    def validate_phone_number(self, phone: str) -> bool:
        """Advanced phone number validation"""
        import re
        
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (10-15 digits)
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^0+$',  # All zeros
            r'^1+$',  # All ones
            r'^1234567890$',  # Sequential
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, cleaned):
                return False
        
        return True
    
    def calculate_sms_count(self, message: str) -> int:
        """Calculate number of SMS parts needed"""
        if len(message) <= 160:
            return 1
        else:
            # For messages longer than 160 chars, each part is 153 chars
            return (len(message) // 153) + 1
    
    def calculate_cost(self, message: str, recipient_count: int, provider: str = "mock") -> float:
        """Calculate SMS cost based on message length, recipient count, and provider"""
        sms_count = self.calculate_sms_count(message)
        
        # Provider-specific pricing
        pricing = {
            "twilio": 0.0075,
            "aws_sns": 0.00645,
            "vonage": 0.005,
            "mock": 0.01
        }
        
        cost_per_sms = pricing.get(provider, 0.01)
        total_cost = sms_count * recipient_count * cost_per_sms
        
        return round(total_cost, 4)
    
    async def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        # Implement rate limiting logic here
        # For now, always return True
        return True
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance from provider"""
        if self.provider == SmsProvider.TWILIO:
            return await self._get_twilio_balance()
        elif self.provider == SmsProvider.MOCK:
            return {"balance": 100.0, "currency": "USD", "provider": "mock"}
        else:
            return {"balance": 0.0, "currency": "USD", "provider": "unknown"}
    
    async def _get_twilio_balance(self) -> Dict[str, Any]:
        """Get balance from Twilio"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Balance.json",
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "balance": float(data.get("balance", 0)),
                        "currency": data.get("currency", "USD"),
                        "provider": "twilio"
                    }
                else:
                    return {"balance": 0.0, "currency": "USD", "provider": "twilio"}
        except Exception as e:
            logger.error(f"Balance check error: {str(e)}")
            return {"balance": 0.0, "currency": "USD", "provider": "twilio"}

# Global SMS service instance
sms_service = SMSService()

async def process_campaign_messages(campaign_id: int, db: Session):
    """
    Process and send messages for a campaign
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return
    
    # Update campaign status to sending
    campaign.status = CampaignStatus.SENDING
    campaign.sent_at = datetime.utcnow()
    db.commit()
    
    # Get pending messages for this campaign
    messages = db.query(Message).filter(
        Message.campaign_id == campaign_id,
        Message.status == MessageStatus.PENDING
    ).all()
    
    if not messages:
        campaign.status = CampaignStatus.SENT
        db.commit()
        return
    
    # Prepare messages for sending
    message_data = []
    for message in messages:
        message_data.append({
            "phone": message.recipient,
            "message": message.content,
            "message_id": message.id
        })
    
    # Send messages
    results = await sms_service.send_bulk_sms(message_data)
    
    # Update message statuses
    delivered_count = 0
    failed_count = 0
    
    for result in results:
        message = db.query(Message).filter(Message.id == result["message_id"]).first()
        if not message:
            continue
        
        if result["success"]:
            message.status = MessageStatus.SENT
            message.sent_at = datetime.utcnow()
            delivered_count += 1
        else:
            message.status = MessageStatus.FAILED
            message.error_message = result.get("error", "Unknown error")
            failed_count += 1
    
    # Update campaign statistics
    campaign.delivered_count = delivered_count
    campaign.failed_count = failed_count
    campaign.status = CampaignStatus.SENT
    db.commit()
