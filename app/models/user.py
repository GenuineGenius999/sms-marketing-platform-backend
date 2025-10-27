from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="client")  # admin or client
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0.0)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contacts = relationship("Contact", back_populates="user")
    contact_groups = relationship("ContactGroup", back_populates="user")
    campaigns = relationship("Campaign", back_populates="user")
    templates = relationship("SmsTemplate", back_populates="user")
    sender_ids = relationship("SenderId", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    reports = relationship("Report", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")
    
    # New relationships for advanced features
    automation_workflows = relationship("AutomationWorkflow", back_populates="user")
    drip_campaigns = relationship("DripCampaign", back_populates="user")
    segment_rules = relationship("SegmentRule", back_populates="user")
    contact_tags = relationship("ContactTag", back_populates="user")
    integrations = relationship("Integration", back_populates="user")
    webhook_endpoints = relationship("WebhookEndpoint", back_populates="user")
    api_tokens = relationship("APIToken", back_populates="user")
