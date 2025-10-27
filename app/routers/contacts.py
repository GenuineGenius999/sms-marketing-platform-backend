from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.contact import Contact, ContactGroup
from app.schemas.contact import Contact as ContactSchema, ContactCreate, ContactUpdate, ContactGroup as ContactGroupSchema, ContactGroupCreate, ContactGroupUpdate
from app.core.deps import get_current_active_user
import pandas as pd
import io

router = APIRouter()

# Contact endpoints
@router.get("/", response_model=list[ContactSchema])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).offset(skip).limit(limit).all()
    return contacts

@router.post("/", response_model=ContactSchema)
async def create_contact(
    contact: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_contact = Contact(
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        user_id=current_user.id,
        group_id=contact.group_id
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.post("/import")
async def import_contacts(
    contacts_data: list[dict],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    imported_count = 0
    errors = []
    
    for i, contact_data in enumerate(contacts_data):
        try:
            # Check if contact already exists
            existing_contact = db.query(Contact).filter(
                Contact.user_id == current_user.id,
                Contact.phone == contact_data.get('phone')
            ).first()
            
            if existing_contact:
                errors.append(f"Row {i+1}: Contact with phone {contact_data.get('phone')} already exists")
                continue
            
            # Validate group_id if provided
            if contact_data.get('group_id'):
                group = db.query(ContactGroup).filter(
                    ContactGroup.id == contact_data.get('group_id'),
                    ContactGroup.user_id == current_user.id
                ).first()
                if not group:
                    errors.append(f"Row {i+1}: Invalid group_id {contact_data.get('group_id')}")
                    continue
            
            # Create contact
            db_contact = Contact(
                name=contact_data.get('name'),
                phone=contact_data.get('phone'),
                email=contact_data.get('email'),
                user_id=current_user.id,
                group_id=contact_data.get('group_id')
            )
            db.add(db_contact)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    db.commit()
    
    return {
        "success": len(errors) == 0,
        "imported": imported_count,
        "errors": errors
    }

@router.get("/{contact_id}", response_model=ContactSchema)
async def read_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactSchema)
async def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    for field, value in contact_update.dict(exclude_unset=True).items():
        setattr(contact, field, value)
    
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

# Contact Group endpoints
@router.get("/groups/", response_model=list[ContactGroupSchema])
async def read_contact_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    groups = db.query(ContactGroup).filter(ContactGroup.user_id == current_user.id).all()
    return groups

@router.post("/groups/", response_model=ContactGroupSchema)
async def create_contact_group(
    group: ContactGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_group = ContactGroup(
        name=group.name,
        description=group.description,
        user_id=current_user.id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/groups/{group_id}", response_model=ContactGroupSchema)
async def read_contact_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    group = db.query(ContactGroup).filter(
        ContactGroup.id == group_id,
        ContactGroup.user_id == current_user.id
    ).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Contact group not found")
    return group

@router.put("/groups/{group_id}", response_model=ContactGroupSchema)
async def update_contact_group(
    group_id: int,
    group_update: ContactGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    group = db.query(ContactGroup).filter(
        ContactGroup.id == group_id,
        ContactGroup.user_id == current_user.id
    ).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Contact group not found")
    
    for field, value in group_update.dict(exclude_unset=True).items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    return group

@router.delete("/groups/{group_id}")
async def delete_contact_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    group = db.query(ContactGroup).filter(
        ContactGroup.id == group_id,
        ContactGroup.user_id == current_user.id
    ).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Contact group not found")
    
    db.delete(group)
    db.commit()
    return {"message": "Contact group deleted successfully"}

# Bulk import endpoint
@router.post("/bulk-import")
async def bulk_import_contacts(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk import contacts from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['name', 'phone', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        successful = 0
        failed = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Check if contact already exists
                existing_contact = db.query(Contact).filter(
                    Contact.email == row['email'],
                    Contact.user_id == current_user.id
                ).first()
                
                if existing_contact:
                    errors.append(f"Row {index + 1}: Contact with email {row['email']} already exists")
                    failed += 1
                    continue
                
                # Create new contact
                contact = Contact(
                    name=row['name'],
                    phone=row['phone'],
                    email=row['email'],
                    user_id=current_user.id
                )
                
                # Handle group assignment if group_name column exists
                if 'group_name' in df.columns and pd.notna(row['group_name']):
                    group = db.query(ContactGroup).filter(
                        ContactGroup.name == row['group_name'],
                        ContactGroup.user_id == current_user.id
                    ).first()
                    
                    if group:
                        contact.group_id = group.id
                
                db.add(contact)
                successful += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                failed += 1
        
        db.commit()
        
        return {
            "successful": successful,
            "failed": failed,
            "total": len(df),
            "errors": errors[:10]  # Limit to first 10 errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")