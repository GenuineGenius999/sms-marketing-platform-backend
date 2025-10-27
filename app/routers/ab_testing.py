from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.ab_testing import ABTestCampaign, ABTestVariant, ABTestRecipient, ABTestResult
from app.schemas.ab_testing import (
    ABTestCampaign as ABTestCampaignSchema,
    ABTestCampaignCreate,
    ABTestCampaignUpdate,
    ABTestVariant as ABTestVariantSchema,
    ABTestVariantCreate,
    ABTestVariantUpdate,
    ABTestRecipient as ABTestRecipientSchema,
    ABTestResult as ABTestResultSchema,
    ABTestStats,
    ABTestRecommendation
)
from app.core.deps import get_current_active_user
from app.services.ab_testing_service import ABTestingService
from datetime import datetime

router = APIRouter()

@router.post("/campaigns", response_model=dict)
async def create_ab_test_campaign(
    campaign_data: ABTestCampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new A/B test campaign"""
    try:
        service = ABTestingService(db)
        result = await service.create_ab_test(
            user_id=current_user.id,
            test_data=campaign_data.dict()
        )
        
        if result.get("success"):
            return {"success": True, "campaign_id": result["campaign_id"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating A/B test: {str(e)}"
        )

@router.get("/campaigns", response_model=List[ABTestCampaignSchema])
async def get_ab_test_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get A/B test campaigns for the current user"""
    campaigns = db.query(ABTestCampaign).filter(
        ABTestCampaign.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return campaigns

@router.get("/campaigns/{campaign_id}", response_model=ABTestCampaignSchema)
async def get_ab_test_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific A/B test campaign"""
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    return campaign

@router.put("/campaigns/{campaign_id}", response_model=ABTestCampaignSchema)
async def update_ab_test_campaign(
    campaign_id: int,
    campaign_update: ABTestCampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an A/B test campaign"""
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    for field, value in campaign_update.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    
    return campaign

@router.post("/campaigns/{campaign_id}/start")
async def start_ab_test_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start an A/B test campaign"""
    try:
        service = ABTestingService(db)
        result = await service.start_ab_test(campaign_id, current_user.id)
        
        if result.get("success"):
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting A/B test: {str(e)}"
        )

@router.post("/campaigns/{campaign_id}/analyze")
async def analyze_ab_test_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze an A/B test campaign"""
    try:
        service = ABTestingService(db)
        result = await service.analyze_ab_test(campaign_id)
        
        if result.get("success"):
            return {"success": True, "analysis": result["analysis"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing A/B test: {str(e)}"
        )

@router.get("/campaigns/{campaign_id}/variants", response_model=List[ABTestVariantSchema])
async def get_ab_test_variants(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get variants for an A/B test campaign"""
    # Verify campaign ownership
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    variants = db.query(ABTestVariant).filter(
        ABTestVariant.campaign_id == campaign_id
    ).all()
    
    return variants

@router.get("/campaigns/{campaign_id}/recipients", response_model=List[ABTestRecipientSchema])
async def get_ab_test_recipients(
    campaign_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recipients for an A/B test campaign"""
    # Verify campaign ownership
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    recipients = db.query(ABTestRecipient).filter(
        ABTestRecipient.campaign_id == campaign_id
    ).offset(skip).limit(limit).all()
    
    return recipients

@router.get("/campaigns/{campaign_id}/results", response_model=List[ABTestResultSchema])
async def get_ab_test_results(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get results for an A/B test campaign"""
    # Verify campaign ownership
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    results = db.query(ABTestResult).filter(
        ABTestResult.campaign_id == campaign_id
    ).all()
    
    return results

@router.get("/stats", response_model=ABTestStats)
async def get_ab_test_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get A/B testing statistics for the current user"""
    try:
        service = ABTestingService(db)
        stats = await service.get_ab_test_stats(current_user.id)
        return ABTestStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting A/B test stats: {str(e)}"
        )

@router.delete("/campaigns/{campaign_id}")
async def delete_ab_test_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an A/B test campaign"""
    campaign = db.query(ABTestCampaign).filter(
        ABTestCampaign.id == campaign_id,
        ABTestCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test campaign not found"
        )
    
    # Delete related records
    db.query(ABTestRecipient).filter(
        ABTestRecipient.campaign_id == campaign_id
    ).delete()
    
    db.query(ABTestResult).filter(
        ABTestResult.campaign_id == campaign_id
    ).delete()
    
    db.query(ABTestVariant).filter(
        ABTestVariant.campaign_id == campaign_id
    ).delete()
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "A/B test campaign deleted successfully"}
