from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])


@router.get("", response_model=List[schemas.PurchaseResponse])
def get_purchases(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    seller_name: Optional[str] = None,
    # scrap_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get all purchases with optional filters"""
    query = db.query(models.Purchase)

    if start_date:
        query = query.filter(models.Purchase.date >= start_date)
    if end_date:
        query = query.filter(models.Purchase.date <= end_date)
    if seller_name:
        query = query.filter(models.Purchase.seller_name.ilike(f"%{seller_name}%"))
    # if scrap_type:
    #     query = query.filter(models.Purchase.scrap_type.ilike(f"%{scrap_type}%"))

    purchases = (
        query.order_by(models.Purchase.date.desc()).offset(skip).limit(limit).all()
    )
    return purchases


@router.get("/{purchase_id}", response_model=schemas.PurchaseResponse)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get a single purchase by ID"""
    purchase = (
        db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.post("", response_model=schemas.PurchaseResponse, status_code=201)
def create_purchase(
    purchase: schemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Create a new purchase"""
    # Calculate total purchase cost
    total_cost = (purchase.quantity * purchase.price_per_unit) + purchase.transport_cost

    db_purchase = models.Purchase(**purchase.dict(), total_purchase_cost=total_cost)

    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)

    # Automatically create expense entry for transport cost
    if purchase.transport_cost > 0:
        transport_expense = models.Expense(
            date=purchase.date,
            category=models.ExpenseCategory.TRANSPORT,
            amount=purchase.transport_cost,
            description=f"Transport cost for purchase from {purchase.seller_name}"
            + (
                f" ({purchase.transport_service})" if purchase.transport_service else ""
            ),
        )
        db.add(transport_expense)
        db.commit()

    return db_purchase


@router.put("/{purchase_id}", response_model=schemas.PurchaseResponse)
def update_purchase(
    purchase_id: int,
    purchase_update: schemas.PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Update a purchase"""
    db_purchase = (
        db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    )
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    update_data = purchase_update.dict(exclude_unset=True)

    # Track if transport cost changed
    old_transport_cost = db_purchase.transport_cost
    transport_cost_changed = "transport_cost" in update_data

    # Recalculate total if quantity or price changed
    quantity = update_data.get("quantity", db_purchase.quantity)
    price_per_unit = update_data.get("price_per_unit", db_purchase.price_per_unit)
    transport_cost = update_data.get("transport_cost", db_purchase.transport_cost)

    if (
        "quantity" in update_data
        or "price_per_unit" in update_data
        or "transport_cost" in update_data
    ):
        update_data["total_purchase_cost"] = (
            quantity * price_per_unit
        ) + transport_cost

    for key, value in update_data.items():
        setattr(db_purchase, key, value)

    db.commit()
    db.refresh(db_purchase)

    # Update or create transport expense if transport cost changed
    if transport_cost_changed:
        # Find existing transport expense for this purchase
        existing_expense = (
            db.query(models.Expense)
            .filter(
                models.Expense.date == db_purchase.date,
                models.Expense.category == models.ExpenseCategory.TRANSPORT,
                models.Expense.description.like(
                    f"%purchase from {db_purchase.seller_name}%"
                ),
            )
            .first()
        )

        if existing_expense:
            if transport_cost > 0:
                # Update existing expense
                existing_expense.amount = transport_cost
                existing_expense.description = (
                    f"Transport cost for purchase from {db_purchase.seller_name}"
                    + (
                        f" ({db_purchase.transport_service})"
                        if db_purchase.transport_service
                        else ""
                    )
                )
            else:
                # Delete expense if transport cost is now 0
                db.delete(existing_expense)
        elif transport_cost > 0:
            # Create new expense if it didn't exist
            transport_expense = models.Expense(
                date=db_purchase.date,
                category=models.ExpenseCategory.TRANSPORT,
                amount=transport_cost,
                description=f"Transport cost for purchase from {db_purchase.seller_name}"
                + (
                    f" ({db_purchase.transport_service})"
                    if db_purchase.transport_service
                    else ""
                ),
            )
            db.add(transport_expense)

        db.commit()

    return db_purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete a purchase"""
    db_purchase = (
        db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    )
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    # Delete associated transport expense if it exists
    if db_purchase.transport_cost > 0:
        existing_expense = (
            db.query(models.Expense)
            .filter(
                models.Expense.date == db_purchase.date,
                models.Expense.category == models.ExpenseCategory.TRANSPORT,
                models.Expense.description.like(
                    f"%purchase from {db_purchase.seller_name}%"
                ),
            )
            .first()
        )

        if existing_expense:
            db.delete(existing_expense)

    db.delete(db_purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}


@router.get("/stats/today")
def get_today_purchases_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get today's purchase statistics"""
    today = date.today()
    result = (
        db.query(func.sum(models.Purchase.total_purchase_cost))
        .filter(models.Purchase.date == today)
        .scalar()
    )

    return {"today_purchases": result or 0}
