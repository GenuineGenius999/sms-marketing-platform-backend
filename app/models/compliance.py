from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class OptInStatus(str, enum.Enum):
    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    PENDING = "pending"
    UNSUBSCRIBED = "unsubscribed"

class ComplianceType(str, enum.Enum):
    TCPA = "tcpa"
    GDPR = "gdpr"
    CAN_SPAM = "can_spam"
    CCPA = "ccpa"

class ContactOptIn(Base):
    __tablename__ = "contact_opt_ins"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)  # OptInStatus
    opt_in_method = Column(String, nullable=True)  # web, sms, email, phone, etc.
    opt_in_source = Column(String, nullable=True)  # website, campaign, import, etc.
    opt_in_timestamp = Column(DateTime(timezone=True), nullable=True)
    opt_out_timestamp = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    consent_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contact = relationship("Contact")
    user = relationship("User")

class ComplianceLog(Base):
    __tablename__ = "compliance_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    action = Column(String, nullable=False)  # opt_in, opt_out, unsubscribe, etc.
    compliance_type = Column(String, nullable=False)  # ComplianceType
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    contact = relationship("Contact")
    campaign = relationship("Campaign")

class UnsubscribeToken(Base):
    __tablename__ = "unsubscribe_tokens"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact")
    user = relationship("User")

class ComplianceSettings(Base):
    __tablename__ = "compliance_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    compliance_type = Column(String, nullable=False)  # ComplianceType
    settings = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")

class MessageCompliance(Base):
    __tablename__ = "message_compliance"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    compliance_checks = Column(JSON, nullable=True)  # Store compliance check results
    opt_out_links = Column(JSON, nullable=True)  # Store opt-out links
    compliance_status = Column(String, default="pending")  # pending, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message")
    reviewer = relationship("User")
