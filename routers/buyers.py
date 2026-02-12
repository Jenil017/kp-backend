from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/buyers", tags=["Buyers"])

@router.get("", response_model=List[schemas.BuyerResponse])
def get_buyers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all buyers with optional search"""
    query = db.query(models.Buyer)
    
    if search:
        query = query.filter(
            (models.Buyer.name.ilike(f"%{search}%")) |
            (models.Buyer.phone.ilike(f"%{search}%"))
        )
    
    buyers = query.order_by(models.Buyer.name).offset(skip).limit(limit).all()
    return buyers

@router.get("/list", response_model=List[schemas.BuyerListResponse])
def get_buyers_list(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get simplified buyers list"""
    buyers = db.query(models.Buyer).order_by(models.Buyer.name).all()
    
    result = []
    for buyer in buyers:
        total_sales = sum(sale.total_amount for sale in buyer.sales)
        total_payments = sum(payment.amount for payment in buyer.payments)
        outstanding = buyer.opening_balance + total_sales - total_payments
        
        result.append({
            "id": buyer.id,
            "name": buyer.name,
            "phone": buyer.phone,
            "outstanding_balance": outstanding
        })
    
    return result

@router.get("/{buyer_id}", response_model=schemas.BuyerResponse)
def get_buyer(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get a single buyer by ID"""
    buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer

@router.post("", response_model=schemas.BuyerResponse, status_code=201)
def create_buyer(
    buyer: schemas.BuyerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new buyer"""
    db_buyer = models.Buyer(**buyer.dict())
    db.add(db_buyer)
    db.commit()
    db.refresh(db_buyer)
    return db_buyer

@router.put("/{buyer_id}", response_model=schemas.BuyerResponse)
def update_buyer(
    buyer_id: int,
    buyer_update: schemas.BuyerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a buyer"""
    db_buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not db_buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    update_data = buyer_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_buyer, key, value)
    
    db.commit()
    db.refresh(db_buyer)
    return db_buyer

@router.delete("/{buyer_id}")
def delete_buyer(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a buyer"""
    db_buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not db_buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    # Check if buyer has sales or payments
    if db_buyer.sales or db_buyer.payments:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete buyer with existing sales or payments"
        )
    
    db.delete(db_buyer)
    db.commit()
    return {"message": "Buyer deleted successfully"}

@router.get("/{buyer_id}/ledger", response_model=schemas.BuyerLedgerResponse)
def get_buyer_ledger(
    buyer_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get buyer ledger (Khata)"""
    buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    # Get sales
    sales_query = db.query(models.Sale).filter(models.Sale.buyer_id == buyer_id)
    if start_date:
        sales_query = sales_query.filter(models.Sale.date >= start_date)
    if end_date:
        sales_query = sales_query.filter(models.Sale.date <= end_date)
    sales = sales_query.order_by(models.Sale.date).all()
    
    # Get payments
    payments_query = db.query(models.Payment).filter(models.Payment.buyer_id == buyer_id)
    if start_date:
        payments_query = payments_query.filter(models.Payment.date >= start_date)
    if end_date:
        payments_query = payments_query.filter(models.Payment.date <= end_date)
    payments = payments_query.order_by(models.Payment.date).all()
    
    # Build ledger entries
    entries = []
    running_balance = buyer.opening_balance
    
    # Combine and sort all transactions
    transactions = []
    
    for sale in sales:
        transactions.append({
            "date": sale.date,
            "type": "SALE",
            "description": f"Sale #{sale.id} - {sale.payment_type.value}",
            "debit": sale.total_amount,
            "credit": 0,
            "obj": sale
        })
    
    for payment in payments:
        transactions.append({
            "date": payment.date,
            "type": "PAYMENT",
            "description": f"Payment - {payment.payment_method}",
            "debit": 0,
            "credit": payment.amount,
            "obj": payment
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x["date"])
    
    for txn in transactions:
        running_balance += txn["debit"] - txn["credit"]
        entries.append(schemas.LedgerEntry(
            date=txn["date"],
            type=txn["type"],
            description=txn["description"],
            debit=txn["debit"],
            credit=txn["credit"],
            balance=running_balance
        ))
    
    total_sales = sum(sale.total_amount for sale in sales)
    total_payments = sum(payment.amount for payment in payments)
    closing_balance = buyer.opening_balance + total_sales - total_payments
    
    return schemas.BuyerLedgerResponse(
        buyer=buyer,
        entries=entries,
        opening_balance=buyer.opening_balance,
        closing_balance=closing_balance
    )

@router.post("/{buyer_id}/payments", response_model=schemas.PaymentResponse)
def add_payment(
    buyer_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Add a payment for a buyer"""
    buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    db_payment = models.Payment(
        date=payment.date,
        buyer_id=buyer_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.get("/{buyer_id}/payments", response_model=List[schemas.PaymentResponse])
def get_buyer_payments(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all payments for a buyer"""
    buyer = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    
    payments = db.query(models.Payment).filter(
        models.Payment.buyer_id == buyer_id
    ).order_by(models.Payment.date.desc()).all()
    
    return payments