from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.models.message import Message, MessageStatus
from app.models.contact import Contact, ContactGroup
from app.models.billing import Transaction, TransactionType, PaymentStatus

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific user"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic stats
        total_campaigns = self.db.query(Campaign).filter(
            Campaign.user_id == user_id
        ).count()
        
        active_campaigns = self.db.query(Campaign).filter(
            Campaign.user_id == user_id,
            Campaign.status == CampaignStatus.ACTIVE
        ).count()
        
        total_contacts = self.db.query(Contact).filter(
            Contact.user_id == user_id
        ).count()
        
        total_messages = self.db.query(Message).join(Campaign).filter(
            Campaign.user_id == user_id
        ).count()
        
        sent_messages = self.db.query(Message).join(Campaign).filter(
            Campaign.user_id == user_id,
            Message.status == MessageStatus.SENT
        ).count()
        
        failed_messages = self.db.query(Message).join(Campaign).filter(
            Campaign.user_id == user_id,
            Message.status == MessageStatus.FAILED
        ).count()
        
        # Calculate delivery rate
        delivery_rate = (sent_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Revenue calculations
        total_spent = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.SMS_COST,
            Transaction.status == PaymentStatus.COMPLETED
        ).scalar() or 0.0
        
        # Daily stats for the period
        daily_stats = self._get_daily_stats(user_id, start_date, end_date)
        
        # Top performing campaigns
        top_campaigns = self._get_top_campaigns(user_id, limit=5)
        
        # Contact engagement
        contact_engagement = self._get_contact_engagement(user_id)
        
        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_contacts": total_contacts,
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "failed_messages": failed_messages,
            "delivery_rate": round(delivery_rate, 2),
            "total_spent": round(total_spent, 2),
            "daily_stats": daily_stats,
            "top_campaigns": top_campaigns,
            "contact_engagement": contact_engagement
        }
    
    def get_platform_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get platform-wide analytics for admin"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # User stats
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        
        # Campaign stats
        total_campaigns = self.db.query(Campaign).count()
        active_campaigns = self.db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).count()
        
        # Message stats
        total_messages = self.db.query(Message).count()
        sent_messages = self.db.query(Message).filter(
            Message.status == MessageStatus.SENT
        ).count()
        failed_messages = self.db.query(Message).filter(
            Message.status == MessageStatus.FAILED
        ).count()
        
        # Revenue stats
        total_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.SMS_COST,
            Transaction.status == PaymentStatus.COMPLETED
        ).scalar() or 0.0
        
        # Top users by activity
        top_users = self._get_top_users(limit=10)
        
        # Daily platform stats
        daily_stats = self._get_platform_daily_stats(start_date, end_date)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "failed_messages": failed_messages,
            "delivery_rate": round((sent_messages / total_messages * 100) if total_messages > 0 else 0, 2),
            "total_revenue": round(total_revenue, 2),
            "top_users": top_users,
            "daily_stats": daily_stats
        }
    
    def _get_daily_stats(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily statistics for a user"""
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Messages sent on this day
            messages_sent = self.db.query(Message).join(Campaign).filter(
                Campaign.user_id == user_id,
                Message.status == MessageStatus.SENT,
                Message.sent_at >= current_date,
                Message.sent_at < next_date
            ).count()
            
            # Revenue for this day
            revenue = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.SMS_COST,
                Transaction.status == PaymentStatus.COMPLETED,
                Transaction.created_at >= current_date,
                Transaction.created_at < next_date
            ).scalar() or 0.0
            
            daily_stats.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "messages_sent": messages_sent,
                "revenue": round(revenue, 2)
            })
            
            current_date = next_date
        
        return daily_stats
    
    def _get_platform_daily_stats(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily platform statistics"""
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Messages sent on this day
            messages_sent = self.db.query(Message).filter(
                Message.status == MessageStatus.SENT,
                Message.sent_at >= current_date,
                Message.sent_at < next_date
            ).count()
            
            # New users on this day
            new_users = self.db.query(User).filter(
                User.created_at >= current_date,
                User.created_at < next_date
            ).count()
            
            # Revenue for this day
            revenue = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.type == TransactionType.SMS_COST,
                Transaction.status == PaymentStatus.COMPLETED,
                Transaction.created_at >= current_date,
                Transaction.created_at < next_date
            ).scalar() or 0.0
            
            daily_stats.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "messages_sent": messages_sent,
                "new_users": new_users,
                "revenue": round(revenue, 2)
            })
            
            current_date = next_date
        
        return daily_stats
    
    def _get_top_campaigns(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing campaigns for a user"""
        campaigns = self.db.query(Campaign).filter(
            Campaign.user_id == user_id
        ).order_by(desc(Campaign.delivered_count)).limit(limit).all()
        
        result = []
        for campaign in campaigns:
            delivery_rate = (campaign.delivered_count / campaign.total_recipients * 100) if campaign.total_recipients > 0 else 0
            
            result.append({
                "id": campaign.id,
                "name": campaign.name,
                "total_recipients": campaign.total_recipients,
                "delivered_count": campaign.delivered_count,
                "failed_count": campaign.failed_count,
                "delivery_rate": round(delivery_rate, 2),
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None
            })
        
        return result
    
    def _get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by activity"""
        users = self.db.query(
            User.id,
            User.name,
            User.email,
            func.count(Campaign.id).label('total_campaigns'),
            func.sum(Campaign.delivered_count).label('total_messages')
        ).join(Campaign, User.id == Campaign.user_id).group_by(
            User.id, User.name, User.email
        ).order_by(desc('total_messages')).limit(limit).all()
        
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "total_campaigns": user.total_campaigns,
                "total_messages": user.total_messages or 0
            })
        
        return result
    
    def _get_contact_engagement(self, user_id: int) -> Dict[str, Any]:
        """Get contact engagement metrics"""
        # Contacts with messages sent
        engaged_contacts = self.db.query(func.count(func.distinct(Message.recipient))).join(
            Campaign, Message.campaign_id == Campaign.id
        ).filter(
            Campaign.user_id == user_id
        ).scalar() or 0
        
        # Total contacts
        total_contacts = self.db.query(Contact).filter(
            Contact.user_id == user_id
        ).count()
        
        # Engagement rate
        engagement_rate = (engaged_contacts / total_contacts * 100) if total_contacts > 0 else 0
        
        return {
            "total_contacts": total_contacts,
            "engaged_contacts": engaged_contacts,
            "engagement_rate": round(engagement_rate, 2)
        }
