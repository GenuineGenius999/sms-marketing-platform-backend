from sqlalchemy.ext.declarative import declarative_base

# Create the declarative base
Base = declarative_base()

from .user import User
from .contact import Contact, ContactGroup
from .campaign import Campaign
from .template import SmsTemplate
from .message import Message
from .sender_id import SenderId
from .billing import Transaction, PaymentMethod, Invoice
from .report import Report, Analytics
from .automation import (
    AutomationWorkflow, AutomationExecution, KeywordTrigger, 
    DripCampaign, DripCampaignStep, DripCampaignContact
)
from .compliance import (
    ContactOptIn, ComplianceLog, UnsubscribeToken, 
    ComplianceSettings, MessageCompliance
)
from .segmentation import (
    SegmentRule, ContactSegment, ContactTag, 
    ContactTagAssignment, ContactBehavior, ContactEngagement
)
from .integration import (
    Integration, IntegrationSync, WebhookEndpoint, 
    WebhookLog, APIToken
)
from .ab_testing import (
    ABTestCampaign, ABTestVariant, ABTestRecipient, ABTestResult
)
from .survey import (
    Survey, SurveyQuestion, SurveyRecipient, SurveyResponse, 
    SurveyAnswer, SurveyAnalytics
)

__all__ = [
    "Base",
    "User",
    "Contact",
    "ContactGroup",
    "Campaign",
    "SmsTemplate",
    "Message",
    "SenderId",
    "Transaction",
    "PaymentMethod",
    "Invoice",
    "Report",
    "Analytics",
    "AutomationWorkflow",
    "AutomationExecution",
    "KeywordTrigger",
    "DripCampaign",
    "DripCampaignStep",
    "DripCampaignContact",
    "ContactOptIn",
    "ComplianceLog",
    "UnsubscribeToken",
    "ComplianceSettings",
    "MessageCompliance",
    "SegmentRule",
    "ContactSegment",
    "ContactTag",
    "ContactTagAssignment",
    "ContactBehavior",
    "ContactEngagement",
    "Integration",
    "IntegrationSync",
    "WebhookEndpoint",
    "WebhookLog",
    "APIToken",
    "ABTestCampaign",
    "ABTestVariant",
    "ABTestRecipient",
    "ABTestResult",
    "Survey",
    "SurveyQuestion",
    "SurveyRecipient",
    "SurveyResponse",
    "SurveyAnswer",
    "SurveyAnalytics"
]
