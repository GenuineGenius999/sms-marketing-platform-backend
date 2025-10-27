from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class TriggerType(str, enum.Enum):
    KEYWORD = "keyword"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    CONTACT_ACTION = "contact_action"
    CAMPAIGN_COMPLETION = "campaign_completion"

class ActionType(str, enum.Enum):
    SEND_SMS = "send_sms"
    ADD_TO_GROUP = "add_to_group"
    REMOVE_FROM_GROUP = "remove_from_group"
    UPDATE_CONTACT = "update_contact"
    SEND_EMAIL = "send_email"
    WEBHOOK_CALL = "webhook_call"

class AutomationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"

class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String, nullable=False)  # TriggerType
    trigger_config = Column(JSON, nullable=True)  # Store trigger-specific config
    action_type = Column(String, nullable=False)  # ActionType
    action_config = Column(JSON, nullable=True)  # Store action-specific config
    status = Column(String, default=AutomationStatus.ACTIVE)  # AutomationStatus
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="automation_workflows")

class AutomationExecution(Base):
    __tablename__ = "automation_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("automation_workflows.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    trigger_data = Column(JSON, nullable=True)
    action_result = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    workflow = relationship("AutomationWorkflow")
    contact = relationship("Contact")
    campaign = relationship("Campaign")

class KeywordTrigger(Base):
    __tablename__ = "keyword_triggers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword = Column(String, nullable=False)
    response_message = Column(Text, nullable=False)
    is_case_sensitive = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

class DripCampaign(Base):
    __tablename__ = "drip_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="drip_campaigns")
    steps = relationship("DripCampaignStep", back_populates="campaign")

class DripCampaignStep(Base):
    __tablename__ = "drip_campaign_steps"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("drip_campaigns.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    delay_days = Column(Integer, default=0)
    delay_hours = Column(Integer, default=0)
    message_template_id = Column(Integer, ForeignKey("sms_templates.id"), nullable=True)
    message_content = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("DripCampaign", back_populates="steps")
    template = relationship("SmsTemplate")

class DripCampaignContact(Base):
    __tablename__ = "drip_campaign_contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("drip_campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    current_step = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    campaign = relationship("DripCampaign")
    contact = relationship("Contact")
