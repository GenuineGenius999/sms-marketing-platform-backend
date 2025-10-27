from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.report import Report, Analytics
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.message import Message, MessageStatus
from app.models.billing import Transaction, TransactionType, PaymentStatus
from app.schemas.report import (
    ReportCreate, ReportResponse, ReportUpdate,
    AnalyticsCreate, AnalyticsResponse,
    CampaignReport, ContactReport, MessageReport, BillingReport, DashboardMetrics
)
from app.core.deps import get_current_active_user, get_admin_user
from app.services.analytics_service import AnalyticsService
from datetime import datetime, timedelta
import json

router = APIRouter()

# Report endpoints
@router.post("/reports", response_model=ReportResponse)
async def create_report(
    report: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new report"""
    db_report = Report(
        user_id=current_user.id,
        name=report.name,
        type=report.type,
        filters=report.filters,
        status="pending"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Generate report data asynchronously
    await generate_report_data(db_report.id, db)
    
    return db_report

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's reports"""
    reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(desc(Report.created_at)).offset(skip).limit(limit).all()
    
    return reports

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific report"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a report"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted successfully"}

# Analytics endpoints
@router.post("/analytics", response_model=AnalyticsResponse)
async def create_analytics(
    analytics: AnalyticsCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create analytics data point"""
    db_analytics = Analytics(
        user_id=current_user.id,
        metric_name=analytics.metric_name,
        metric_value=analytics.metric_value,
        metric_type=analytics.metric_type,
        tags=analytics.tags
    )
    
    db.add(db_analytics)
    db.commit()
    db.refresh(db_analytics)
    
    return db_analytics

@router.get("/analytics", response_model=List[AnalyticsResponse])
async def get_analytics(
    metric_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics data"""
    query = db.query(Analytics).filter(Analytics.user_id == current_user.id)
    
    if metric_name:
        query = query.filter(Analytics.metric_name == metric_name)
    
    if start_date:
        query = query.filter(Analytics.timestamp >= start_date)
    
    if end_date:
        query = query.filter(Analytics.timestamp <= end_date)
    
    analytics = query.order_by(desc(Analytics.timestamp)).all()
    
    return analytics

# Dashboard metrics
@router.get("/dashboard-metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard metrics"""
    
    # Campaign metrics
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    campaign_metrics = CampaignReport(
        campaign_id=0,
        campaign_name="All Campaigns",
        total_recipients=sum(c.total_recipients for c in campaigns),
        sent_messages=sum(c.delivered_count + c.failed_count for c in campaigns),
        delivered_messages=sum(c.delivered_count for c in campaigns),
        failed_messages=sum(c.failed_count for c in campaigns),
        delivery_rate=0.0,
        cost=0.0,
        created_at=datetime.utcnow()
    )
    
    if campaign_metrics.sent_messages > 0:
        campaign_metrics.delivery_rate = (campaign_metrics.delivered_messages / campaign_metrics.sent_messages) * 100
    
    # Contact metrics
    total_contacts = db.query(Contact).filter(Contact.user_id == current_user.id).count()
    active_contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.is_active == True
    ).count()
    
    # New contacts this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_contacts_this_month = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.created_at >= start_of_month
    ).count()
    
    contact_metrics = ContactReport(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        new_contacts_this_month=new_contacts_this_month,
        contacts_by_group={}  # Would need to implement contact groups
    )
    
    # Message metrics
    total_messages = db.query(Message).filter(Message.user_id == current_user.id).count()
    sent_messages = db.query(Message).filter(
        Message.user_id == current_user.id,
        Message.status == MessageStatus.SENT
    ).count()
    delivered_messages = db.query(Message).filter(
        Message.user_id == current_user.id,
        Message.status == MessageStatus.DELIVERED
    ).count()
    failed_messages = db.query(Message).filter(
        Message.user_id == current_user.id,
        Message.status == MessageStatus.FAILED
    ).count()
    
    message_metrics = MessageReport(
        total_messages=total_messages,
        sent_messages=sent_messages,
        delivered_messages=delivered_messages,
        failed_messages=failed_messages,
        messages_by_status={
            "sent": sent_messages,
            "delivered": delivered_messages,
            "failed": failed_messages
        },
        messages_by_day=[]  # Would need to implement daily breakdown
    )
    
    # Billing metrics
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.SMS_COST,
        Transaction.status == PaymentStatus.COMPLETED
    ).scalar() or 0.0
    
    total_recharged = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.RECHARGE,
        Transaction.status == PaymentStatus.COMPLETED
    ).scalar() or 0.0
    
    transactions_count = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).count()
    
    billing_metrics = BillingReport(
        total_spent=total_spent,
        total_recharged=total_recharged,
        current_balance=current_user.balance,
        spending_by_month=[],  # Would need to implement monthly breakdown
        transactions_count=transactions_count
    )
    
    return DashboardMetrics(
        campaigns=campaign_metrics,
        contacts=contact_metrics,
        messages=message_metrics,
        billing=billing_metrics
    )

# Campaign-specific reports
@router.get("/campaigns/{campaign_id}/report", response_model=CampaignReport)
async def get_campaign_report(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed report for a specific campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get campaign messages
    messages = db.query(Message).filter(Message.campaign_id == campaign_id).all()
    
    sent_messages = len([m for m in messages if m.status == MessageStatus.SENT])
    delivered_messages = len([m for m in messages if m.status == MessageStatus.DELIVERED])
    failed_messages = len([m for m in messages if m.status == MessageStatus.FAILED])
    
    delivery_rate = (delivered_messages / sent_messages * 100) if sent_messages > 0 else 0
    
    return CampaignReport(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        total_recipients=campaign.total_recipients,
        sent_messages=sent_messages,
        delivered_messages=delivered_messages,
        failed_messages=failed_messages,
        delivery_rate=delivery_rate,
        cost=campaign.delivered_count * 0.01,  # Assuming $0.01 per SMS
        created_at=campaign.created_at
    )

async def generate_report_data(report_id: int, db: Session):
    """Generate report data asynchronously"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return
    
    try:
        # Generate report data based on type
        if report.type == "campaign":
            data = await generate_campaign_report_data(report, db)
        elif report.type == "contact":
            data = await generate_contact_report_data(report, db)
        elif report.type == "message":
            data = await generate_message_report_data(report, db)
        elif report.type == "billing":
            data = await generate_billing_report_data(report, db)
        else:
            data = {}
        
        # Update report with data
        report.data = data
        report.status = "completed"
        db.commit()
        
    except Exception as e:
        report.status = "failed"
        report.data = {"error": str(e)}
        db.commit()

async def generate_campaign_report_data(report: Report, db: Session):
    """Generate campaign report data"""
    # Implementation would depend on report filters
    return {"message": "Campaign report data generated"}

async def generate_contact_report_data(report: Report, db: Session):
    """Generate contact report data"""
    return {"message": "Contact report data generated"}

async def generate_message_report_data(report: Report, db: Session):
    """Generate message report data"""
    return {"message": "Message report data generated"}

async def generate_billing_report_data(report: Report, db: Session):
    """Generate billing report data"""
    return {"message": "Billing report data generated"}

# Comprehensive analytics endpoints
@router.get("/analytics")
async def get_user_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for the current user"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_user_analytics(current_user.id, days)

@router.get("/admin/analytics/platform")
async def get_platform_analytics(
    days: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get platform-wide analytics for admin"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_platform_analytics(days)
