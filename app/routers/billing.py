from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.billing import Transaction, PaymentMethod, Invoice, TransactionType, PaymentStatus
from app.schemas.billing import (
    TransactionCreate, TransactionResponse, TransactionUpdate,
    PaymentMethodCreate, PaymentMethodResponse, PaymentMethodUpdate,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate,
    BillingStats, PaymentIntent, PaymentIntentResponse
)
from app.core.deps import get_current_active_user
from datetime import datetime, timedelta
import uuid

router = APIRouter()

# Transaction endpoints
@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    db_transaction = Transaction(
        user_id=current_user.id,
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        reference_id=transaction.reference_id,
        status=PaymentStatus.PENDING
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's transactions"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
    
    return transactions

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    for field, value in transaction_update.dict(exclude_unset=True).items():
        setattr(transaction, field, value)
    
    db.commit()
    db.refresh(transaction)
    
    return transaction

# Payment method endpoints
@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def create_payment_method(
    payment_method: PaymentMethodCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new payment method"""
    # If this is set as default, unset other defaults
    if payment_method.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == "true"
        ).update({"is_default": "false"})
    
    db_payment_method = PaymentMethod(
        user_id=current_user.id,
        method_type=payment_method.method_type,
        provider_id=payment_method.provider_id,
        is_default="true" if payment_method.is_default else "false"
    )
    
    db.add(db_payment_method)
    db.commit()
    db.refresh(db_payment_method)
    
    return db_payment_method

@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's payment methods"""
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_active == "true"
    ).all()
    
    return payment_methods

@router.put("/payment-methods/{method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    method_id: int,
    payment_method_update: PaymentMethodUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a payment method"""
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # If setting as default, unset other defaults
    if payment_method_update.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == "true"
        ).update({"is_default": "false"})
    
    for field, value in payment_method_update.dict(exclude_unset=True).items():
        if field == "is_default":
            setattr(payment_method, field, "true" if value else "false")
        elif field == "is_active":
            setattr(payment_method, field, "true" if value else "false")
        else:
            setattr(payment_method, field, value)
    
    db.commit()
    db.refresh(payment_method)
    
    return payment_method

@router.delete("/payment-methods/{method_id}")
async def delete_payment_method(
    method_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a payment method"""
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    db.delete(payment_method)
    db.commit()
    
    return {"message": "Payment method deleted successfully"}

# Invoice endpoints
@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's invoices"""
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()
    
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific invoice"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

# Billing stats
@router.get("/stats", response_model=BillingStats)
async def get_billing_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get billing statistics"""
    # Current balance
    current_balance = current_user.balance
    
    # Total spent (SMS costs)
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.SMS_COST,
        Transaction.status == PaymentStatus.COMPLETED
    ).scalar() or 0.0
    
    # Total recharged
    total_recharged = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.RECHARGE,
        Transaction.status == PaymentStatus.COMPLETED
    ).scalar() or 0.0
    
    # Pending amount
    pending_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == PaymentStatus.PENDING
    ).scalar() or 0.0
    
    # SMS cost this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    sms_cost_this_month = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.SMS_COST,
        Transaction.status == PaymentStatus.COMPLETED,
        Transaction.created_at >= start_of_month
    ).scalar() or 0.0
    
    # Transaction count
    transaction_count = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).count()
    
    return BillingStats(
        current_balance=current_balance,
        total_spent=total_spent,
        total_recharged=total_recharged,
        pending_amount=pending_amount,
        sms_cost_this_month=sms_cost_this_month,
        transaction_count=transaction_count
    )

# Payment processing
@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_intent: PaymentIntent,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for recharging balance"""
    # In a real implementation, this would integrate with Stripe, PayPal, etc.
    # For now, we'll create a mock payment intent
    
    client_secret = f"pi_mock_{uuid.uuid4().hex[:24]}"
    payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
    
    # Create a pending transaction
    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.RECHARGE,
        amount=payment_intent.amount,
        description=f"Balance recharge - {payment_intent.description or 'Manual recharge'}",
        reference_id=payment_intent_id,
        status=PaymentStatus.PENDING
    )
    
    db.add(transaction)
    db.commit()
    
    return PaymentIntentResponse(
        client_secret=client_secret,
        payment_intent_id=payment_intent_id,
        amount=payment_intent.amount,
        currency=payment_intent.currency
    )

@router.post("/payment-intent/{payment_intent_id}/confirm")
async def confirm_payment(
    payment_intent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Confirm a payment and update user balance"""
    # Find the transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference_id == payment_intent_id,
        Transaction.user_id == current_user.id,
        Transaction.status == PaymentStatus.PENDING
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    
    # Update transaction status
    transaction.status = PaymentStatus.COMPLETED
    
    # Update user balance
    current_user.balance += transaction.amount
    
    db.commit()
    
    return {"message": "Payment confirmed successfully", "new_balance": current_user.balance}
