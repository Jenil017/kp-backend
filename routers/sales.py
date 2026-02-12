from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/sales", tags=["Sales"])

@router.get("", response_model=List[schemas.SaleResponse])
def get_sales(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    buyer_id: Optional[int] = None,
    payment_type: Optional[schemas.PaymentType] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all sales with optional filters"""
    query = db.query(models.Sale)
    
    if start_date:
        query = query.filter(models.Sale.date >= start_date)
    if end_date:
        query = query.filter(models.Sale.date <= end_date)
    if buyer_id:
        query = query.filter(models.Sale.buyer_id == buyer_id)
    if payment_type:
        query = query.filter(models.Sale.payment_type == payment_type)
    
    sales = query.order_by(models.Sale.date.desc()).offset(skip).limit(limit).all()
    return sales

@router.get("/{sale_id}", response_model=schemas.SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get a single sale by ID"""
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.post("", response_model=schemas.SaleResponse, status_code=201)
def create_sale(
    sale: schemas.SaleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new sale with items"""
    # Calculate total from items
    total_amount = 0
    for item in sale.sale_items:
        total_amount += item.quantity * item.price_per_unit
    
    # Create sale
    db_sale = models.Sale(
        date=sale.date,
        buyer_id=sale.buyer_id,
        payment_type=sale.payment_type,
        payment_received_now=sale.payment_received_now,
        total_amount=total_amount,
        notes=sale.notes
    )
    
    db.add(db_sale)
    db.flush()  # Get sale ID
    
    # Create sale items
    for item in sale.sale_items:
        db_item = models.SaleItem(
            sale_id=db_sale.id,
            product_type_id=item.product_type_id,
            quantity=item.quantity,
            unit=item.unit,
            price_per_unit=item.price_per_unit,
            total_price=item.quantity * item.price_per_unit
        )
        db.add(db_item)
    
    # If payment received, create payment record
    if sale.payment_received_now > 0:
        payment = models.Payment(
            date=sale.date,
            buyer_id=sale.buyer_id,
            amount=sale.payment_received_now,
            payment_method="Cash",
            notes=f"Payment for Sale #{db_sale.id}"
        )
        db.add(payment)
    
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.put("/{sale_id}", response_model=schemas.SaleResponse)
def update_sale(
    sale_id: int,
    sale_update: schemas.SaleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a sale"""
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    update_data = sale_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_sale, key, value)
    
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a sale"""
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    db.delete(db_sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

@router.get("/stats/today")
def get_today_sales_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get today's sales statistics"""
    today = date.today()
    result = db.query(func.sum(models.Sale.total_amount)).filter(
        models.Sale.date == today
    ).scalar()
    
    return {"today_sales": result or 0}