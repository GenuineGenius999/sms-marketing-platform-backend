from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.automation import (
    AutomationWorkflow, AutomationExecution, KeywordTrigger, 
    DripCampaign, DripCampaignStep, DripCampaignContact
)
from app.core.deps import get_current_active_user
from app.services.automation_service import AutomationService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Pydantic schemas
class AutomationWorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Optional[dict] = None
    action_type: str
    action_config: Optional[dict] = None
    status: str = "active"

class AutomationWorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: Optional[dict]
    action_type: str
    action_config: Optional[dict]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class KeywordTriggerCreate(BaseModel):
    keyword: str
    response_message: str
    is_case_sensitive: bool = False

class KeywordTriggerResponse(BaseModel):
    id: int
    keyword: str
    response_message: str
    is_case_sensitive: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DripCampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[dict]

class DripCampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Automation Workflow endpoints
@router.post("/workflows", response_model=AutomationWorkflowResponse)
async def create_automation_workflow(
    workflow: AutomationWorkflowCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new automation workflow"""
    automation_service = AutomationService(db)
    
    result = await automation_service.create_automation_workflow(
        workflow_data=workflow.dict(),
        user_id=current_user.id
    )
    
    if result.get("success"):
        workflow_obj = db.query(AutomationWorkflow).filter(
            AutomationWorkflow.id == result["workflow_id"]
        ).first()
        return workflow_obj
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )

@router.get("/workflows", response_model=List[AutomationWorkflowResponse])
async def get_automation_workflows(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get automation workflows for the current user"""
    workflows = db.query(AutomationWorkflow).filter(
        AutomationWorkflow.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return workflows

@router.get("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
async def get_automation_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific automation workflow"""
    workflow = db.query(AutomationWorkflow).filter(
        AutomationWorkflow.id == workflow_id,
        AutomationWorkflow.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return workflow

@router.put("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
async def update_automation_workflow(
    workflow_id: int,
    workflow_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an automation workflow"""
    workflow = db.query(AutomationWorkflow).filter(
        AutomationWorkflow.id == workflow_id,
        AutomationWorkflow.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    for field, value in workflow_update.items():
        if hasattr(workflow, field):
            setattr(workflow, field, value)
    
    workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    
    return workflow

@router.delete("/workflows/{workflow_id}")
async def delete_automation_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an automation workflow"""
    workflow = db.query(AutomationWorkflow).filter(
        AutomationWorkflow.id == workflow_id,
        AutomationWorkflow.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    db.delete(workflow)
    db.commit()
    
    return {"message": "Workflow deleted successfully"}

# Keyword Trigger endpoints
@router.post("/keyword-triggers", response_model=KeywordTriggerResponse)
async def create_keyword_trigger(
    trigger: KeywordTriggerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new keyword trigger"""
    keyword_trigger = KeywordTrigger(
        user_id=current_user.id,
        keyword=trigger.keyword,
        response_message=trigger.response_message,
        is_case_sensitive=trigger.is_case_sensitive
    )
    
    db.add(keyword_trigger)
    db.commit()
    db.refresh(keyword_trigger)
    
    return keyword_trigger

@router.get("/keyword-triggers", response_model=List[KeywordTriggerResponse])
async def get_keyword_triggers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get keyword triggers for the current user"""
    triggers = db.query(KeywordTrigger).filter(
        KeywordTrigger.user_id == current_user.id
    ).all()
    
    return triggers

@router.put("/keyword-triggers/{trigger_id}", response_model=KeywordTriggerResponse)
async def update_keyword_trigger(
    trigger_id: int,
    trigger_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a keyword trigger"""
    trigger = db.query(KeywordTrigger).filter(
        KeywordTrigger.id == trigger_id,
        KeywordTrigger.user_id == current_user.id
    ).first()
    
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword trigger not found"
        )
    
    for field, value in trigger_update.items():
        if hasattr(trigger, field):
            setattr(trigger, field, value)
    
    db.commit()
    db.refresh(trigger)
    
    return trigger

@router.delete("/keyword-triggers/{trigger_id}")
async def delete_keyword_trigger(
    trigger_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a keyword trigger"""
    trigger = db.query(KeywordTrigger).filter(
        KeywordTrigger.id == trigger_id,
        KeywordTrigger.user_id == current_user.id
    ).first()
    
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword trigger not found"
        )
    
    db.delete(trigger)
    db.commit()
    
    return {"message": "Keyword trigger deleted successfully"}

# Drip Campaign endpoints
@router.post("/drip-campaigns", response_model=DripCampaignResponse)
async def create_drip_campaign(
    campaign: DripCampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new drip campaign"""
    automation_service = AutomationService(db)
    
    result = await automation_service.create_drip_campaign(
        campaign_data=campaign.dict(),
        user_id=current_user.id
    )
    
    if result.get("success"):
        drip_campaign = db.query(DripCampaign).filter(
            DripCampaign.id == result["campaign_id"]
        ).first()
        return drip_campaign
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )

@router.get("/drip-campaigns", response_model=List[DripCampaignResponse])
async def get_drip_campaigns(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get drip campaigns for the current user"""
    campaigns = db.query(DripCampaign).filter(
        DripCampaign.user_id == current_user.id
    ).all()
    
    return campaigns

@router.post("/drip-campaigns/{campaign_id}/add-contact")
async def add_contact_to_drip_campaign(
    campaign_id: int,
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a contact to a drip campaign"""
    automation_service = AutomationService(db)
    
    result = await automation_service.add_contact_to_drip_campaign(
        campaign_id=campaign_id,
        contact_id=contact_id
    )
    
    if result.get("success"):
        return {"message": "Contact added to drip campaign successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )

@router.get("/drip-campaigns/{campaign_id}/contacts")
async def get_drip_campaign_contacts(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contacts in a drip campaign"""
    # Verify campaign belongs to user
    campaign = db.query(DripCampaign).filter(
        DripCampaign.id == campaign_id,
        DripCampaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found"
        )
    
    contacts = db.query(DripCampaignContact).filter(
        DripCampaignContact.campaign_id == campaign_id,
        DripCampaignContact.is_active == True
    ).all()
    
    return {
        "campaign_id": campaign_id,
        "contacts": [
            {
                "contact_id": contact.contact_id,
                "current_step": contact.current_step,
                "started_at": contact.started_at,
                "is_active": contact.is_active
            }
            for contact in contacts
        ]
    }

# Automation execution endpoints
@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    contact_id: int,
    trigger_data: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute an automation workflow"""
    automation_service = AutomationService(db)
    
    result = await automation_service.execute_workflow(
        workflow_id=workflow_id,
        contact_id=contact_id,
        trigger_data=trigger_data
    )
    
    if result.get("success"):
        return {"message": "Workflow executed successfully", "result": result}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )

@router.get("/executions")
async def get_automation_executions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get automation executions for the current user"""
    executions = db.query(AutomationExecution).join(
        AutomationWorkflow
    ).filter(
        AutomationWorkflow.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return {
        "executions": [
            {
                "id": exec.id,
                "workflow_id": exec.workflow_id,
                "contact_id": exec.contact_id,
                "status": exec.status,
                "executed_at": exec.executed_at,
                "error_message": exec.error_message
            }
            for exec in executions
        ]
    }
