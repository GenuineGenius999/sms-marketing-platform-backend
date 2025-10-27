from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: str = "client"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    balance: Optional[float] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    role: str
    is_active: bool
    balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
