from datetime import date, timedelta
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
import models
from datetime import datetime


def seed_analytics():
    print("Seeding analytics data...")
    db = SessionLocal()

    try:
        # Check if we have product types, if not, create one
        product_type = db.query(models.ProductType).first()
        if not product_type:
            product_type = models.ProductType(
                name="Generic Wood", description="Default"
            )
            db.add(product_type)
            db.commit()
            db.refresh(product_type)

        # Check if we have a buyer, if not, create one
        buyer = db.query(models.Buyer).first()
        if not buyer:
            buyer = models.Buyer(
                name="Demo Client", phone="1234567890", address="123 Main St"
            )
            db.add(buyer)
            db.commit()
            db.refresh(buyer)

        today = date.today()

        # Generate data for past 12 months
        for i in range(12):
            month_date = today - timedelta(days=30 * i)
            # Adjust to be somewhat random within the month

            # 1. Create a Purchase
            purchase = models.Purchase(
                date=month_date,
                seller_name=f"Seller {i}",
                quantity=random.uniform(100, 1000),
                price_per_unit=random.uniform(10, 50),
                total_purchase_cost=random.uniform(1000, 5000),
                scrap_type="Wood",
                notes="Seeded purchase",
            )
            db.add(purchase)

            # 2. Create a Sales
            # We need a sale item linked to product type
            sale_amount = random.uniform(2000, 8000)
            sale = models.Sale(
                date=month_date,
                buyer_id=buyer.id,
                payment_type=models.PaymentType.PAID,
                total_amount=sale_amount,
                notes="Seeded sale",
            )
            db.add(sale)
            db.commit()  # Commit to get sale ID
            db.refresh(sale)

            sale_item = models.SaleItem(
                sale_id=sale.id,
                product_type_id=product_type.id,
                quantity=random.uniform(50, 500),
                price_per_unit=random.uniform(20, 100),
                total_price=sale_amount,
            )
            db.add(sale_item)

            # 3. Create an Expense
            expense = models.Expense(
                date=month_date,
                category=random.choice(list(models.ExpenseCategory)),
                amount=random.uniform(100, 1000),
                description=f"Monthly expense {i}",
            )
            db.add(expense)

        db.commit()
        print("Successfully seeded analytics data for the last 12 months!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_analytics()
