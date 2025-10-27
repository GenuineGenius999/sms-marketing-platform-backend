from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.ab_testing import TestStatus, TestType

class ABTestVariantBase(BaseModel):
    variant_name: str
    variant_type: TestType
    message_content: Optional[str] = None
    sender_id: Optional[str] = None
    send_time: Optional[datetime] = None
    subject_line: Optional[str] = None

class ABTestVariantCreate(ABTestVariantBase):
    pass

class ABTestVariantUpdate(BaseModel):
    message_content: Optional[str] = None
    sender_id: Optional[str] = None
    send_time: Optional[datetime] = None
    subject_line: Optional[str] = None

class ABTestVariant(ABTestVariantBase):
    id: int
    campaign_id: int
    recipients_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    replied_count: int
    conversion_rate: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ABTestCampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: TestType
    traffic_split: float = 0.5
    test_duration_days: int = 7
    minimum_sample_size: int = 100
    confidence_level: float = 0.95

class ABTestCampaignCreate(ABTestCampaignBase):
    variants: List[ABTestVariantCreate]

class ABTestCampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TestStatus] = None
    traffic_split: Optional[float] = None
    test_duration_days: Optional[int] = None
    minimum_sample_size: Optional[int] = None
    confidence_level: Optional[float] = None

class ABTestCampaign(ABTestCampaignBase):
    id: int
    user_id: int
    status: TestStatus
    variant_a_recipients: int
    variant_b_recipients: int
    variant_a_delivered: int
    variant_b_delivered: int
    variant_a_opened: int
    variant_b_opened: int
    variant_a_clicked: int
    variant_b_clicked: int
    variant_a_replied: int
    variant_b_replied: int
    variant_a_conversion_rate: float
    variant_b_conversion_rate: float
    statistical_significance: float
    winner_variant: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include variants in response
    variants: List[ABTestVariant] = []

    class Config:
        from_attributes = True

class ABTestRecipientBase(BaseModel):
    contact_id: int
    variant_id: int

class ABTestRecipientCreate(ABTestRecipientBase):
    pass

class ABTestRecipient(ABTestRecipientBase):
    id: int
    campaign_id: int
    is_delivered: bool
    is_opened: bool
    is_clicked: bool
    is_replied: bool
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ABTestResultBase(BaseModel):
    variant_a_metrics: Optional[Dict[str, Any]] = None
    variant_b_metrics: Optional[Dict[str, Any]] = None
    statistical_significance: float
    confidence_interval: Optional[Dict[str, float]] = None
    p_value: float
    effect_size: float
    winner_variant: Optional[str] = None
    improvement_percentage: float
    recommendation: Optional[str] = None

class ABTestResultCreate(ABTestResultBase):
    campaign_id: int
    sample_size: int
    test_duration_hours: float

class ABTestResult(ABTestResultBase):
    id: int
    campaign_id: int
    sample_size: int
    test_duration_hours: float
    analysis_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class ABTestStats(BaseModel):
    total_tests: int
    running_tests: int
    completed_tests: int
    successful_tests: int
    average_improvement: float
    most_effective_test_type: str

class ABTestRecommendation(BaseModel):
    test_type: TestType
    recommended_split: float
    estimated_duration: int
    expected_improvement: float
    confidence_level: float
