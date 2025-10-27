from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from app.models.survey import SurveyStatus, QuestionType

class SurveyQuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    question_order: int
    is_required: bool = True
    options: Optional[List[str]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    scale_labels: Optional[Dict[str, str]] = None

class SurveyQuestionCreate(SurveyQuestionBase):
    pass

class SurveyQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    question_order: Optional[int] = None
    is_required: Optional[bool] = None
    options: Optional[List[str]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    scale_labels: Optional[Dict[str, str]] = None

class SurveyQuestion(SurveyQuestionBase):
    id: int
    survey_id: int
    response_count: int
    average_rating: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    thank_you_message: Optional[str] = None
    is_anonymous: bool = False
    allow_multiple_responses: bool = False
    max_responses: Optional[int] = None
    sms_keyword: Optional[str] = None
    sender_id: Optional[str] = None
    auto_send: bool = False

class SurveyCreate(SurveyBase):
    questions: List[SurveyQuestionCreate]

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SurveyStatus] = None
    welcome_message: Optional[str] = None
    thank_you_message: Optional[str] = None
    is_anonymous: Optional[bool] = None
    allow_multiple_responses: Optional[bool] = None
    max_responses: Optional[int] = None
    sms_keyword: Optional[str] = None
    sender_id: Optional[str] = None
    auto_send: Optional[bool] = None

class Survey(SurveyBase):
    id: int
    user_id: int
    status: SurveyStatus
    total_sent: int
    total_responses: int
    completion_rate: float
    average_rating: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Include questions in response
    questions: List[SurveyQuestion] = []

    class Config:
        from_attributes = True

class SurveyRecipientBase(BaseModel):
    contact_id: Optional[int] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class SurveyRecipientCreate(SurveyRecipientBase):
    pass

class SurveyRecipient(SurveyRecipientBase):
    id: int
    survey_id: int
    is_sent: bool
    is_responded: bool
    is_completed: bool
    sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SurveyAnswerBase(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_number: Optional[int] = None
    answer_boolean: Optional[bool] = None
    answer_json: Optional[Dict[str, Any]] = None

class SurveyAnswerCreate(SurveyAnswerBase):
    pass

class SurveyAnswer(SurveyAnswerBase):
    id: int
    response_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SurveyResponseBase(BaseModel):
    is_anonymous: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SurveyResponseCreate(SurveyResponseBase):
    answers: List[SurveyAnswerCreate]

class SurveyResponse(SurveyResponseBase):
    id: int
    survey_id: int
    recipient_id: Optional[int] = None
    contact_id: Optional[int] = None
    is_completed: bool
    completion_percentage: float
    total_questions: int
    answered_questions: int
    time_spent_seconds: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Include answers in response
    answers: List[SurveyAnswer] = []

    class Config:
        from_attributes = True

class SurveyAnalyticsBase(BaseModel):
    total_recipients: int
    total_sent: int
    total_responses: int
    total_completed: int
    send_rate: float
    response_rate: float
    completion_rate: float
    question_analytics: Optional[Dict[str, Any]] = None
    average_completion_time: float
    median_completion_time: float
    average_rating: float
    rating_distribution: Optional[Dict[str, int]] = None

class SurveyAnalytics(SurveyAnalyticsBase):
    id: int
    survey_id: int
    calculated_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    class Config:
        from_attributes = True

class SurveyStats(BaseModel):
    total_surveys: int
    active_surveys: int
    completed_surveys: int
    total_responses: int
    average_response_rate: float
    most_popular_question_type: str

class SurveyRecommendation(BaseModel):
    survey_type: str
    recommended_questions: int
    estimated_duration: int
    expected_response_rate: float
    best_send_time: str
