from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class SurveyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TEXT = "text"
    RATING = "rating"
    YES_NO = "yes_no"
    SCALE = "scale"

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(SurveyStatus), default=SurveyStatus.DRAFT)
    
    # Survey Configuration
    welcome_message = Column(Text, nullable=True)
    thank_you_message = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    allow_multiple_responses = Column(Boolean, default=False)
    max_responses = Column(Integer, nullable=True)
    
    # SMS Configuration
    sms_keyword = Column(String, nullable=True)  # Keyword to trigger survey
    sender_id = Column(String, nullable=True)
    auto_send = Column(Boolean, default=False)
    
    # Analytics
    total_sent = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")
    recipients = relationship("SurveyRecipient", back_populates="survey", cascade="all, delete-orphan")

class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    question_order = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    
    # Question Configuration
    options = Column(JSON, nullable=True)  # For multiple choice, single choice
    min_value = Column(Integer, nullable=True)  # For rating/scale questions
    max_value = Column(Integer, nullable=True)  # For rating/scale questions
    scale_labels = Column(JSON, nullable=True)  # For scale questions
    
    # Analytics
    response_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    survey = relationship("Survey", back_populates="questions")
    answers = relationship("SurveyAnswer", back_populates="question", cascade="all, delete-orphan")

class SurveyRecipient(Base):
    __tablename__ = "survey_recipients"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Recipient Status
    is_sent = Column(Boolean, default=False)
    is_responded = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    survey = relationship("Survey", back_populates="recipients")
    contact = relationship("Contact")
    response = relationship("SurveyResponse", back_populates="recipient", uselist=False)

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("survey_recipients.id"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    
    # Response Data
    is_anonymous = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Response Status
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Analytics
    total_questions = Column(Integer, default=0)
    answered_questions = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    survey = relationship("Survey", back_populates="responses")
    recipient = relationship("SurveyRecipient", back_populates="response")
    contact = relationship("Contact")
    answers = relationship("SurveyAnswer", back_populates="response", cascade="all, delete-orphan")

class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    
    # Answer Data
    answer_text = Column(Text, nullable=True)
    answer_number = Column(Integer, nullable=True)
    answer_boolean = Column(Boolean, nullable=True)
    answer_json = Column(JSON, nullable=True)  # For complex answers
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")

class SurveyAnalytics(Base):
    __tablename__ = "survey_analytics"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    
    # Analytics Data
    total_recipients = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    
    # Response Rates
    send_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    
    # Question Analytics
    question_analytics = Column(JSON, nullable=True)  # Per-question analytics
    
    # Time Analytics
    average_completion_time = Column(Float, default=0.0)
    median_completion_time = Column(Float, default=0.0)
    
    # Rating Analytics
    average_rating = Column(Float, default=0.0)
    rating_distribution = Column(JSON, nullable=True)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    survey = relationship("Survey")
