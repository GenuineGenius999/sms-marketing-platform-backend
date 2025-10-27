from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class IntegrationType(str, enum.Enum):
    CRM = "crm"
    EMAIL_MARKETING = "email_marketing"
    ECOMMERCE = "ecommerce"
    ANALYTICS = "analytics"
    WEBHOOK = "webhook"
    API = "api"

class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    integration_type = Column(String, nullable=False)  # IntegrationType
    provider = Column(String, nullable=False)  # salesforce, hubspot, mailchimp, etc.
    config = Column(JSON, nullable=True)  # Store integration configuration
    credentials = Column(JSON, nullable=True)  # Store encrypted credentials
    status = Column(String, default=IntegrationStatus.PENDING)  # IntegrationStatus
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(Integer, default=3600)  # Sync frequency in seconds
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="integrations")

class IntegrationSync(Base):
    __tablename__ = "integration_syncs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    sync_type = Column(String, nullable=False)  # contacts, campaigns, analytics, etc.
    status = Column(String, default="pending")  # pending, running, completed, failed
    records_processed = Column(Integer, default=0)
    records_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    integration = relationship("Integration")

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=True)  # List of events to listen for
    secret_key = Column(String, nullable=True)  # For webhook verification
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="webhook_endpoints")

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempts = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    next_retry = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")  # pending, delivered, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    endpoint = relationship("WebhookEndpoint")

class APIToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    permissions = Column(JSON, nullable=True)  # List of API permissions
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="api_tokens")
