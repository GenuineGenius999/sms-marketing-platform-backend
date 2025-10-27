from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class TestStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TestType(str, enum.Enum):
    MESSAGE_CONTENT = "message_content"
    SEND_TIME = "send_time"
    SENDER_ID = "sender_id"
    SUBJECT_LINE = "subject_line"

class ABTestCampaign(Base):
    __tablename__ = "ab_test_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(Enum(TestType), nullable=False)
    status = Column(Enum(TestStatus), default=TestStatus.DRAFT)
    
    # Test Configuration
    traffic_split = Column(Float, default=0.5)  # 50/50 split by default
    test_duration_days = Column(Integer, default=7)
    minimum_sample_size = Column(Integer, default=100)
    confidence_level = Column(Float, default=0.95)  # 95% confidence
    
    # Test Results
    variant_a_recipients = Column(Integer, default=0)
    variant_b_recipients = Column(Integer, default=0)
    variant_a_delivered = Column(Integer, default=0)
    variant_b_delivered = Column(Integer, default=0)
    variant_a_opened = Column(Integer, default=0)
    variant_b_opened = Column(Integer, default=0)
    variant_a_clicked = Column(Integer, default=0)
    variant_b_clicked = Column(Integer, default=0)
    variant_a_replied = Column(Integer, default=0)
    variant_b_replied = Column(Integer, default=0)
    
    # Statistical Results
    variant_a_conversion_rate = Column(Float, default=0.0)
    variant_b_conversion_rate = Column(Float, default=0.0)
    statistical_significance = Column(Float, default=0.0)
    winner_variant = Column(String, nullable=True)  # 'A', 'B', or 'inconclusive'
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    variants = relationship("ABTestVariant", back_populates="campaign")
    results = relationship("ABTestResult", back_populates="campaign")

class ABTestVariant(Base):
    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("ab_test_campaigns.id"), nullable=False)
    variant_name = Column(String, nullable=False)  # 'A' or 'B'
    variant_type = Column(Enum(TestType), nullable=False)
    
    # Variant Content
    message_content = Column(Text, nullable=True)
    sender_id = Column(String, nullable=True)
    send_time = Column(DateTime(timezone=True), nullable=True)
    subject_line = Column(String, nullable=True)
    
    # Performance Metrics
    recipients_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    campaign = relationship("ABTestCampaign", back_populates="variants")
    recipients = relationship("ABTestRecipient", back_populates="variant")

class ABTestRecipient(Base):
    __tablename__ = "ab_test_recipients"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("ab_test_campaigns.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    
    # Recipient Status
    is_delivered = Column(Boolean, default=False)
    is_opened = Column(Boolean, default=False)
    is_clicked = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("ABTestCampaign")
    variant = relationship("ABTestVariant", back_populates="recipients")
    contact = relationship("Contact")

class ABTestResult(Base):
    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("ab_test_campaigns.id"), nullable=False)
    
    # Statistical Analysis
    variant_a_metrics = Column(Text, nullable=True)  # JSON string
    variant_b_metrics = Column(Text, nullable=True)  # JSON string
    statistical_significance = Column(Float, default=0.0)
    confidence_interval = Column(Text, nullable=True)  # JSON string
    p_value = Column(Float, default=0.0)
    effect_size = Column(Float, default=0.0)
    
    # Winner Analysis
    winner_variant = Column(String, nullable=True)
    improvement_percentage = Column(Float, default=0.0)
    recommendation = Column(Text, nullable=True)
    
    # Analysis Metadata
    sample_size = Column(Integer, default=0)
    test_duration_hours = Column(Float, default=0.0)
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("ABTestCampaign", back_populates="results")
