from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ContactBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class ContactCreate(ContactBase):
    group_id: Optional[int] = None

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    group_id: Optional[int] = None

class Contact(ContactBase):
    id: int
    user_id: int
    group_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContactGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class ContactGroupCreate(ContactGroupBase):
    pass

class ContactGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ContactGroup(ContactGroupBase):
    id: int
    user_id: int
    contact_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
