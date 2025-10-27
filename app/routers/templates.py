from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.template import SmsTemplate
from app.schemas.template import SmsTemplate as SmsTemplateSchema, SmsTemplateCreate, SmsTemplateUpdate
from app.core.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=list[SmsTemplateSchema])
async def read_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    templates = db.query(SmsTemplate).filter(SmsTemplate.user_id == current_user.id).all()
    return templates

@router.post("/", response_model=SmsTemplateSchema)
async def create_template(
    template: SmsTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_template = SmsTemplate(
        name=template.name,
        content=template.content,
        user_id=current_user.id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/{template_id}", response_model=SmsTemplateSchema)
async def read_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    template = db.query(SmsTemplate).filter(
        SmsTemplate.id == template_id,
        SmsTemplate.user_id == current_user.id
    ).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=SmsTemplateSchema)
async def update_template(
    template_id: int,
    template_update: SmsTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    template = db.query(SmsTemplate).filter(
        SmsTemplate.id == template_id,
        SmsTemplate.user_id == current_user.id
    ).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    template = db.query(SmsTemplate).filter(
        SmsTemplate.id == template_id,
        SmsTemplate.user_id == current_user.id
    ).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}
