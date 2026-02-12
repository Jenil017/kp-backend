from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import date, timedelta
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard-summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get dashboard summary statistics"""
    today = date.today()

    # Today's stats
    today_purchases = (
        db.query(func.sum(models.Purchase.total_purchase_cost))
        .filter(models.Purchase.date == today)
        .scalar()
        or 0
    )

    today_sales = (
        db.query(func.sum(models.Sale.total_amount))
        .filter(models.Sale.date == today)
        .scalar()
        or 0
    )

    today_expenses = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.date == today)
        .scalar()
        or 0
    )

    # Overall stats
    total_purchases = (
        db.query(func.sum(models.Purchase.total_purchase_cost)).scalar() or 0
    )
    total_sales = db.query(func.sum(models.Sale.total_amount)).scalar() or 0
    total_expenses = db.query(func.sum(models.Expense.amount)).scalar() or 0

    total_profit = total_sales - total_purchases - total_expenses

    # Total receivable from all buyers
    total_receivable = 0
    buyers = db.query(models.Buyer).all()
    for buyer in buyers:
        total_sales_buyer = sum(sale.total_amount for sale in buyer.sales)
        total_payments_buyer = sum(payment.amount for payment in buyer.payments)
        total_receivable += (
            buyer.opening_balance + total_sales_buyer - total_payments_buyer
        )

    return schemas.DashboardSummary(
        today_purchases=today_purchases,
        today_sales=today_sales,
        today_expenses=today_expenses,
        total_purchases=total_purchases,
        total_sales=total_sales,
        total_expenses=total_expenses,
        total_profit=total_profit,
        total_receivable=total_receivable,
    )


@router.get("/monthly-stats")
def get_monthly_stats(
    months: int = Query(default=12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get monthly statistics for charts"""
    end_date = date.today()

    # Calculate the list of months we want to show (last 'months' months including current)
    month_list = []
    curr = end_date.replace(day=1)
    for _ in range(months):
        month_list.append((curr.year, curr.month))
        # Decrement month
        if curr.month == 1:
            curr = curr.replace(year=curr.year - 1, month=12)
        else:
            curr = curr.replace(month=curr.month - 1)

    month_list.reverse()  # Sort ascending

    # Start date is the first day of the oldest month
    start_date = date(month_list[0][0], month_list[0][1], 1)

    # Get monthly purchases
    purchase_results = (
        db.query(
            extract("year", models.Purchase.date).label("year"),
            extract("month", models.Purchase.date).label("month"),
            func.sum(models.Purchase.total_purchase_cost).label("total"),
        )
        .filter(models.Purchase.date >= start_date)
        .group_by(
            extract("year", models.Purchase.date),
            extract("month", models.Purchase.date),
        )
        .all()
    )

    # Get monthly sales
    sales_results = (
        db.query(
            extract("year", models.Sale.date).label("year"),
            extract("month", models.Sale.date).label("month"),
            func.sum(models.Sale.total_amount).label("total"),
        )
        .filter(models.Sale.date >= start_date)
        .group_by(extract("year", models.Sale.date), extract("month", models.Sale.date))
        .all()
    )

    # Get monthly expenses
    expense_results = (
        db.query(
            extract("year", models.Expense.date).label("year"),
            extract("month", models.Expense.date).label("month"),
            func.sum(models.Expense.amount).label("total"),
        )
        .filter(models.Expense.date >= start_date)
        .group_by(
            extract("year", models.Expense.date), extract("month", models.Expense.date)
        )
        .all()
    )

    # Create dictionaries for easy lookup
    purchase_dict = {
        f"{int(r.year)}-{int(r.month):02d}": r.total for r in purchase_results
    }
    sales_dict = {f"{int(r.year)}-{int(r.month):02d}": r.total for r in sales_results}
    expense_dict = {
        f"{int(r.year)}-{int(r.month):02d}": r.total for r in expense_results
    }

    # Build monthly stats list
    monthly_stats = []
    for year, month in month_list:
        month_key = f"{year}-{month:02d}"
        # Create a date object for formatting logic
        month_date = date(year, month, 1)

        purchases = purchase_dict.get(month_key, 0)
        sales = sales_dict.get(month_key, 0)
        expenses = expense_dict.get(month_key, 0)
        profit = sales - purchases - expenses

        monthly_stats.append(
            {
                "month": month_date.strftime("%b %Y"),
                "purchases": purchases,
                "sales": sales,
                "expenses": expenses,
                "profit": profit,
            }
        )

    return monthly_stats


@router.get("/product-sales")
def get_product_sales_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get sales statistics by product type"""
    query = (
        db.query(
            models.ProductType.name,
            func.sum(models.SaleItem.quantity).label("total_quantity"),
            func.sum(models.SaleItem.total_price).label("total_amount"),
        )
        .join(models.SaleItem, models.ProductType.id == models.SaleItem.product_type_id)
        .join(models.Sale, models.SaleItem.sale_id == models.Sale.id)
    )

    if start_date:
        query = query.filter(models.Sale.date >= start_date)
    if end_date:
        query = query.filter(models.Sale.date <= end_date)

    results = query.group_by(models.ProductType.name).all()

    return [
        {
            "product_name": r.name,
            "total_quantity": r.total_quantity or 0,
            "total_amount": r.total_amount or 0,
        }
        for r in results
    ]


@router.get("/top-buyers")
def get_top_buyers(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get top buyers by outstanding amount"""
    buyers = db.query(models.Buyer).all()

    buyer_stats = []
    for buyer in buyers:
        total_sales = sum(sale.total_amount for sale in buyer.sales)
        total_payments = sum(payment.amount for payment in buyer.payments)
        outstanding = buyer.opening_balance + total_sales - total_payments

        if outstanding > 0:
            buyer_stats.append(
                {"buyer_name": buyer.name, "outstanding_amount": outstanding}
            )

    # Sort by outstanding amount (descending)
    buyer_stats.sort(key=lambda x: x["outstanding_amount"], reverse=True)

    return buyer_stats[:limit]


@router.get("/full-report")
def get_full_analytics_report(
    months: int = Query(default=12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get full analytics report"""
    monthly_stats = get_monthly_stats(months, db, current_user)
    product_sales = get_product_sales_stats(None, None, db, current_user)
    top_buyers = get_top_buyers(10, db, current_user)

    return {
        "monthly_stats": monthly_stats,
        "product_sales": product_sales,
        "top_buyers": top_buyers,
    }
