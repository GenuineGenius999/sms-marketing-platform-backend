from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.billing import TransactionType, PaymentStatus

class TransactionBase(BaseModel):
    type: TransactionType
    amount: float
    description: Optional[str] = None
    reference_id: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    reference_id: Optional[str] = None

class Transaction(TransactionBase):
    id: int
    user_id: int
    status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionResponse(Transaction):
    pass

class PaymentMethodBase(BaseModel):
    method_type: str
    provider_id: str
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(BaseModel):
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class PaymentMethod(PaymentMethodBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentMethodResponse(PaymentMethod):
    pass

class InvoiceBase(BaseModel):
    amount: float
    tax_amount: float = 0.0
    due_date: Optional[datetime] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    paid_at: Optional[datetime] = None

class Invoice(InvoiceBase):
    id: int
    user_id: int
    invoice_number: str
    total_amount: float
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InvoiceResponse(Invoice):
    pass

class BillingStats(BaseModel):
    current_balance: float
    total_spent: float
    total_recharged: float
    pending_amount: float
    sms_cost_this_month: float
    transaction_count: int

class PaymentIntent(BaseModel):
    amount: float
    currency: str = "USD"
    payment_method_id: Optional[str] = None
    description: Optional[str] = None

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str
