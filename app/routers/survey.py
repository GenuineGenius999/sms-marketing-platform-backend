from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.survey import Survey, SurveyQuestion, SurveyRecipient, SurveyResponse, SurveyAnswer, SurveyAnalytics
from app.schemas.survey import (
    Survey as SurveySchema,
    SurveyCreate,
    SurveyUpdate,
    SurveyQuestion as SurveyQuestionSchema,
    SurveyQuestionCreate,
    SurveyQuestionUpdate,
    SurveyRecipient as SurveyRecipientSchema,
    SurveyRecipientCreate,
    SurveyResponse as SurveyResponseSchema,
    SurveyResponseCreate,
    SurveyAnswer as SurveyAnswerSchema,
    SurveyAnalytics as SurveyAnalyticsSchema,
    SurveyStats,
    SurveyRecommendation
)
from app.core.deps import get_current_active_user
from app.services.survey_service import SurveyService
from datetime import datetime

router = APIRouter()

@router.post("/surveys", response_model=dict)
async def create_survey(
    survey_data: SurveyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new survey"""
    try:
        service = SurveyService(db)
        result = await service.create_survey(
            user_id=current_user.id,
            survey_data=survey_data.dict()
        )
        
        if result.get("success"):
            return {"success": True, "survey_id": result["survey_id"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating survey: {str(e)}"
        )

@router.get("/surveys", response_model=List[SurveySchema])
async def get_surveys(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get surveys for the current user"""
    surveys = db.query(Survey).filter(
        Survey.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return surveys

@router.get("/surveys/{survey_id}", response_model=SurveySchema)
async def get_survey(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific survey"""
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    return survey

@router.put("/surveys/{survey_id}", response_model=SurveySchema)
async def update_survey(
    survey_id: int,
    survey_update: SurveyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a survey"""
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    for field, value in survey_update.dict(exclude_unset=True).items():
        setattr(survey, field, value)
    
    db.commit()
    db.refresh(survey)
    
    return survey

@router.post("/surveys/{survey_id}/recipients")
async def add_survey_recipients(
    survey_id: int,
    recipients: List[SurveyRecipientCreate],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add recipients to a survey"""
    try:
        service = SurveyService(db)
        result = await service.add_recipients(
            survey_id=survey_id,
            user_id=current_user.id,
            recipient_data=[r.dict() for r in recipients]
        )
        
        if result.get("success"):
            return {"success": True, "added_count": result["added_count"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding recipients: {str(e)}"
        )

@router.post("/surveys/{survey_id}/send")
async def send_survey(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send survey to recipients"""
    try:
        service = SurveyService(db)
        result = await service.send_survey(survey_id, current_user.id)
        
        if result.get("success"):
            return {"success": True, "sent_count": result["sent_count"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending survey: {str(e)}"
        )

@router.post("/surveys/{survey_id}/responses")
async def submit_survey_response(
    survey_id: int,
    response_data: SurveyResponseCreate,
    db: Session = Depends(get_db)
):
    """Submit a survey response"""
    try:
        service = SurveyService(db)
        result = await service.process_survey_response(
            survey_id=survey_id,
            response_data=response_data.dict()
        )
        
        if result.get("success"):
            return {"success": True, "response_id": result["response_id"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting response: {str(e)}"
        )

@router.get("/surveys/{survey_id}/responses", response_model=List[SurveyResponseSchema])
async def get_survey_responses(
    survey_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get responses for a survey"""
    # Verify survey ownership
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    responses = db.query(SurveyResponse).filter(
        SurveyResponse.survey_id == survey_id
    ).offset(skip).limit(limit).all()
    
    return responses

@router.get("/surveys/{survey_id}/recipients", response_model=List[SurveyRecipientSchema])
async def get_survey_recipients(
    survey_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recipients for a survey"""
    # Verify survey ownership
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    recipients = db.query(SurveyRecipient).filter(
        SurveyRecipient.survey_id == survey_id
    ).offset(skip).limit(limit).all()
    
    return recipients

@router.get("/surveys/{survey_id}/analytics", response_model=SurveyAnalyticsSchema)
async def get_survey_analytics(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a survey"""
    # Verify survey ownership
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Get latest analytics
    analytics = db.query(SurveyAnalytics).filter(
        SurveyAnalytics.survey_id == survey_id
    ).order_by(SurveyAnalytics.calculated_at.desc()).first()
    
    if not analytics:
        # Calculate analytics if not exists
        try:
            service = SurveyService(db)
            result = await service.calculate_survey_analytics(survey_id)
            if result.get("success"):
                analytics = db.query(SurveyAnalytics).filter(
                    SurveyAnalytics.survey_id == survey_id
                ).order_by(SurveyAnalytics.calculated_at.desc()).first()
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error calculating analytics"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating analytics: {str(e)}"
            )
    
    return analytics

@router.post("/surveys/{survey_id}/analytics/calculate")
async def calculate_survey_analytics(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate analytics for a survey"""
    # Verify survey ownership
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    try:
        service = SurveyService(db)
        result = await service.calculate_survey_analytics(survey_id)
        
        if result.get("success"):
            return {"success": True, "analytics": result["analytics"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating analytics: {str(e)}"
        )

@router.get("/surveys/{survey_id}/questions", response_model=List[SurveyQuestionSchema])
async def get_survey_questions(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get questions for a survey"""
    # Verify survey ownership
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    questions = db.query(SurveyQuestion).filter(
        SurveyQuestion.survey_id == survey_id
    ).order_by(SurveyQuestion.question_order).all()
    
    return questions

@router.get("/stats", response_model=SurveyStats)
async def get_survey_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get survey statistics for the current user"""
    try:
        service = SurveyService(db)
        stats = await service.get_survey_stats(current_user.id)
        return SurveyStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting survey stats: {str(e)}"
        )

@router.delete("/surveys/{survey_id}")
async def delete_survey(
    survey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a survey"""
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Delete related records
    db.query(SurveyAnswer).join(SurveyResponse).filter(
        SurveyResponse.survey_id == survey_id
    ).delete(synchronize_session=False)
    
    db.query(SurveyResponse).filter(
        SurveyResponse.survey_id == survey_id
    ).delete()
    
    db.query(SurveyRecipient).filter(
        SurveyRecipient.survey_id == survey_id
    ).delete()
    
    db.query(SurveyQuestion).filter(
        SurveyQuestion.survey_id == survey_id
    ).delete()
    
    db.query(SurveyAnalytics).filter(
        SurveyAnalytics.survey_id == survey_id
    ).delete()
    
    db.delete(survey)
    db.commit()
    
    return {"message": "Survey deleted successfully"}
