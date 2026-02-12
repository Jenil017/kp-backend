from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Enum,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# Enums
class PaymentType(str, enum.Enum):
    PAID = "Paid"
    PARTIAL = "Partial"
    CREDIT = "Credit"


class ExpenseCategory(str, enum.Enum):
    RENT = "Rent"
    ELECTRICITY = "Electricity"
    WATER = "Water"
    LABOUR = "Labour"
    TRANSPORT = "Transport"
    TAX = "Tax"
    OTHER = "Other"


# Users Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Product Types Master Table
class ProductType(Base):
    __tablename__ = "product_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sale_items = relationship("SaleItem", back_populates="product_type")


# Buyers Table (Customers)
class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    opening_balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sales = relationship("Sale", back_populates="buyer")
    payments = relationship("Payment", back_populates="buyer")

    @property
    def total_sales(self):
        return sum(sale.total_amount for sale in self.sales)

    @property
    def total_payments(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def outstanding_balance(self):
        return self.opening_balance + self.total_sales - self.total_payments


# Purchases Table (Scrap Purchase)
class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    seller_name = Column(String(255), nullable=False)
    seller_phone = Column(String(20), nullable=True)
    pickup_location = Column(Text, nullable=True)
    scrap_type = Column(String(100), nullable=True)
    transport_service = Column(String(100), nullable=True)
    transport_cost = Column(Float, default=0.0)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="kg")
    price_per_unit = Column(Float, nullable=False)
    total_purchase_cost = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Sales Table
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    payment_received_now = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    buyer = relationship("Buyer", back_populates="sales")
    sale_items = relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan"
    )


# Sale Items Table
class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_type_id = Column(Integer, ForeignKey("product_types.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="kg")
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationships
    sale = relationship("Sale", back_populates="sale_items")
    product_type = relationship("ProductType", back_populates="sale_items")


# Payments Table (Customer Payments)
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100), default="Cash")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    buyer = relationship("Buyer", back_populates="payments")


# Expenses Table
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
