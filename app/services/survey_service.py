import json
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.survey import (
    Survey, SurveyQuestion, SurveyRecipient, SurveyResponse, 
    SurveyAnswer, SurveyAnalytics, SurveyStatus, QuestionType
)
from app.models.contact import Contact
from app.models.user import User
from app.services.sms_service import SMSService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SurveyService:
    def __init__(self, db: Session):
        self.db = db
        self.sms_service = SMSService()

    async def create_survey(self, user_id: int, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new survey"""
        try:
            # Create the main survey
            survey = Survey(
                user_id=user_id,
                title=survey_data["title"],
                description=survey_data.get("description"),
                welcome_message=survey_data.get("welcome_message"),
                thank_you_message=survey_data.get("thank_you_message"),
                is_anonymous=survey_data.get("is_anonymous", False),
                allow_multiple_responses=survey_data.get("allow_multiple_responses", False),
                max_responses=survey_data.get("max_responses"),
                sms_keyword=survey_data.get("sms_keyword"),
                sender_id=survey_data.get("sender_id"),
                auto_send=survey_data.get("auto_send", False),
                status=SurveyStatus.DRAFT
            )
            
            self.db.add(survey)
            self.db.commit()
            self.db.refresh(survey)
            
            # Create questions
            for question_data in survey_data.get("questions", []):
                question = SurveyQuestion(
                    survey_id=survey.id,
                    question_text=question_data["question_text"],
                    question_type=question_data["question_type"],
                    question_order=question_data["question_order"],
                    is_required=question_data.get("is_required", True),
                    options=question_data.get("options"),
                    min_value=question_data.get("min_value"),
                    max_value=question_data.get("max_value"),
                    scale_labels=question_data.get("scale_labels")
                )
                self.db.add(question)
            
            self.db.commit()
            
            return {"success": True, "survey_id": survey.id}
            
        except Exception as e:
            logger.error(f"Error creating survey: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_recipients(self, survey_id: int, user_id: int, recipient_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add recipients to a survey"""
        try:
            survey = self.db.query(Survey).filter(
                Survey.id == survey_id,
                Survey.user_id == user_id
            ).first()
            
            if not survey:
                return {"success": False, "error": "Survey not found"}
            
            added_count = 0
            for recipient_info in recipient_data:
                # Check if recipient already exists
                existing = self.db.query(SurveyRecipient).filter(
                    SurveyRecipient.survey_id == survey_id,
                    SurveyRecipient.contact_id == recipient_info.get("contact_id"),
                    SurveyRecipient.phone_number == recipient_info.get("phone_number")
                ).first()
                
                if existing:
                    continue
                
                recipient = SurveyRecipient(
                    survey_id=survey_id,
                    contact_id=recipient_info.get("contact_id"),
                    phone_number=recipient_info.get("phone_number"),
                    email=recipient_info.get("email")
                )
                self.db.add(recipient)
                added_count += 1
            
            self.db.commit()
            
            return {"success": True, "added_count": added_count}
            
        except Exception as e:
            logger.error(f"Error adding recipients: {str(e)}")
            return {"success": False, "error": str(e)}

    async def send_survey(self, survey_id: int, user_id: int) -> Dict[str, Any]:
        """Send survey to recipients"""
        try:
            survey = self.db.query(Survey).filter(
                Survey.id == survey_id,
                Survey.user_id == user_id
            ).first()
            
            if not survey:
                return {"success": False, "error": "Survey not found"}
            
            if survey.status != SurveyStatus.DRAFT:
                return {"success": False, "error": "Survey is not in draft status"}
            
            # Get recipients
            recipients = self.db.query(SurveyRecipient).filter(
                SurveyRecipient.survey_id == survey_id,
                SurveyRecipient.is_sent == False
            ).all()
            
            if not recipients:
                return {"success": False, "error": "No recipients found"}
            
            # Update survey status
            survey.status = SurveyStatus.ACTIVE
            survey.started_at = datetime.utcnow()
            
            sent_count = 0
            for recipient in recipients:
                # Send SMS with survey link
                message = self._create_survey_message(survey, recipient)
                
                if recipient.phone_number:
                    result = await self.sms_service.send_sms(
                        phone=recipient.phone_number,
                        message=message,
                        sender_id=survey.sender_id
                    )
                    
                    if result.get("success"):
                        recipient.is_sent = True
                        recipient.sent_at = datetime.utcnow()
                        sent_count += 1
            
            survey.total_sent = sent_count
            self.db.commit()
            
            return {"success": True, "sent_count": sent_count}
            
        except Exception as e:
            logger.error(f"Error sending survey: {str(e)}")
            return {"success": False, "error": str(e)}

    def _create_survey_message(self, survey: Survey, recipient: SurveyRecipient) -> str:
        """Create SMS message for survey"""
        message = f"📋 {survey.title}\n\n"
        
        if survey.welcome_message:
            message += f"{survey.welcome_message}\n\n"
        
        message += f"Reply '{survey.sms_keyword}' to start the survey"
        
        if survey.thank_you_message:
            message += f"\n\n{survey.thank_you_message}"
        
        return message

    async def process_survey_response(self, survey_id: int, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a survey response"""
        try:
            survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                return {"success": False, "error": "Survey not found"}
            
            # Create response record
            response = SurveyResponse(
                survey_id=survey_id,
                contact_id=response_data.get("contact_id"),
                is_anonymous=response_data.get("is_anonymous", False),
                ip_address=response_data.get("ip_address"),
                user_agent=response_data.get("user_agent"),
                started_at=datetime.utcnow()
            )
            
            self.db.add(response)
            self.db.commit()
            self.db.refresh(response)
            
            # Process answers
            total_questions = len(survey.questions)
            answered_questions = 0
            
            for answer_data in response_data.get("answers", []):
                answer = SurveyAnswer(
                    response_id=response.id,
                    question_id=answer_data["question_id"],
                    answer_text=answer_data.get("answer_text"),
                    answer_number=answer_data.get("answer_number"),
                    answer_boolean=answer_data.get("answer_boolean"),
                    answer_json=answer_data.get("answer_json")
                )
                self.db.add(answer)
                
                if any([answer_data.get("answer_text"), 
                       answer_data.get("answer_number") is not None,
                       answer_data.get("answer_boolean") is not None]):
                    answered_questions += 1
            
            # Update response completion
            response.total_questions = total_questions
            response.answered_questions = answered_questions
            response.completion_percentage = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
            response.is_completed = response.completion_percentage >= 80  # 80% completion threshold
            response.completed_at = datetime.utcnow() if response.is_completed else None
            
            # Update survey analytics
            survey.total_responses += 1
            if response.is_completed:
                survey.completion_rate = (survey.total_responses / survey.total_sent) * 100 if survey.total_sent > 0 else 0
            
            self.db.commit()
            
            return {"success": True, "response_id": response.id}
            
        except Exception as e:
            logger.error(f"Error processing survey response: {str(e)}")
            return {"success": False, "error": str(e)}

    async def calculate_survey_analytics(self, survey_id: int) -> Dict[str, Any]:
        """Calculate analytics for a survey"""
        try:
            survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                return {"success": False, "error": "Survey not found"}
            
            # Get all responses
            responses = self.db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey_id
            ).all()
            
            # Get all questions
            questions = self.db.query(SurveyQuestion).filter(
                SurveyQuestion.survey_id == survey_id
            ).all()
            
            # Calculate basic metrics
            total_responses = len(responses)
            completed_responses = len([r for r in responses if r.is_completed])
            completion_rate = (completed_responses / total_responses) * 100 if total_responses > 0 else 0
            
            # Calculate question analytics
            question_analytics = {}
            for question in questions:
                answers = self.db.query(SurveyAnswer).filter(
                    SurveyAnswer.question_id == question.id
                ).all()
                
                if question.question_type == QuestionType.RATING:
                    ratings = [a.answer_number for a in answers if a.answer_number is not None]
                    if ratings:
                        question_analytics[question.id] = {
                            "average_rating": sum(ratings) / len(ratings),
                            "total_responses": len(ratings),
                            "rating_distribution": self._calculate_rating_distribution(ratings)
                        }
                elif question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
                    if question.options:
                        option_counts = {option: 0 for option in question.options}
                        for answer in answers:
                            if answer.answer_text in option_counts:
                                option_counts[answer.answer_text] += 1
                        question_analytics[question.id] = {
                            "option_counts": option_counts,
                            "total_responses": len(answers)
                        }
            
            # Calculate average completion time
            completion_times = []
            for response in responses:
                if response.completed_at and response.started_at:
                    time_diff = (response.completed_at - response.started_at).total_seconds()
                    completion_times.append(time_diff)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            median_completion_time = sorted(completion_times)[len(completion_times)//2] if completion_times else 0
            
            # Create analytics record
            analytics = SurveyAnalytics(
                survey_id=survey_id,
                total_recipients=survey.total_sent,
                total_sent=survey.total_sent,
                total_responses=total_responses,
                total_completed=completed_responses,
                send_rate=100.0,  # Assuming all recipients were sent
                response_rate=(total_responses / survey.total_sent) * 100 if survey.total_sent > 0 else 0,
                completion_rate=completion_rate,
                question_analytics=question_analytics,
                average_completion_time=avg_completion_time,
                median_completion_time=median_completion_time,
                average_rating=self._calculate_overall_rating(question_analytics),
                rating_distribution=self._calculate_overall_rating_distribution(question_analytics)
            )
            
            self.db.add(analytics)
            self.db.commit()
            
            return {
                "success": True,
                "analytics": {
                    "total_responses": total_responses,
                    "completed_responses": completed_responses,
                    "completion_rate": completion_rate,
                    "average_completion_time": avg_completion_time,
                    "question_analytics": question_analytics
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating survey analytics: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calculate_rating_distribution(self, ratings: List[int]) -> Dict[str, int]:
        """Calculate rating distribution"""
        distribution = {}
        for rating in ratings:
            distribution[str(rating)] = distribution.get(str(rating), 0) + 1
        return distribution

    def _calculate_overall_rating(self, question_analytics: Dict[str, Any]) -> float:
        """Calculate overall average rating"""
        ratings = []
        for q_id, analytics in question_analytics.items():
            if "average_rating" in analytics:
                ratings.append(analytics["average_rating"])
        return sum(ratings) / len(ratings) if ratings else 0.0

    def _calculate_overall_rating_distribution(self, question_analytics: Dict[str, Any]) -> Dict[str, int]:
        """Calculate overall rating distribution"""
        distribution = {}
        for q_id, analytics in question_analytics.items():
            if "rating_distribution" in analytics:
                for rating, count in analytics["rating_distribution"].items():
                    distribution[rating] = distribution.get(rating, 0) + count
        return distribution

    async def get_survey_stats(self, user_id: int) -> Dict[str, Any]:
        """Get survey statistics for a user"""
        try:
            surveys = self.db.query(Survey).filter(Survey.user_id == user_id).all()
            
            total_surveys = len(surveys)
            active_surveys = len([s for s in surveys if s.status == SurveyStatus.ACTIVE])
            completed_surveys = len([s for s in surveys if s.status == SurveyStatus.COMPLETED])
            
            total_responses = sum(s.total_responses for s in surveys)
            avg_response_rate = sum(s.completion_rate for s in surveys) / total_surveys if total_surveys > 0 else 0
            
            # Most popular question type
            question_types = []
            for survey in surveys:
                for question in survey.questions:
                    question_types.append(question.question_type.value)
            
            most_popular = max(set(question_types), key=question_types.count) if question_types else "text"
            
            return {
                "total_surveys": total_surveys,
                "active_surveys": active_surveys,
                "completed_surveys": completed_surveys,
                "total_responses": total_responses,
                "average_response_rate": avg_response_rate,
                "most_popular_question_type": most_popular
            }
            
        except Exception as e:
            logger.error(f"Error getting survey stats: {str(e)}")
            return {"success": False, "error": str(e)}
