from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import date, datetime
from enum import Enum


# Enums
class PaymentType(str, Enum):
    PAID = "Paid"
    PARTIAL = "Partial"
    CREDIT = "Credit"


class ExpenseCategory(str, Enum):
    RENT = "Rent"
    ELECTRICITY = "Electricity"
    WATER = "Water"
    LABOUR = "Labour"
    TRANSPORT = "Transport"
    TAX = "Tax"
    OTHER = "Other"


# ============== USER SCHEMAS ==============
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ============== PRODUCT TYPE SCHEMAS ==============
class ProductTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProductTypeCreate(ProductTypeBase):
    pass


class ProductTypeResponse(ProductTypeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== BUYER SCHEMAS ==============
class BuyerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    opening_balance: float = 0.0


class BuyerCreate(BuyerBase):
    pass


class BuyerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    opening_balance: Optional[float] = None


class BuyerResponse(BuyerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    total_sales: float = 0.0
    total_payments: float = 0.0
    outstanding_balance: float = 0.0

    class Config:
        from_attributes = True


class BuyerListResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    outstanding_balance: float


# ============== PURCHASE SCHEMAS ==============
class PurchaseBase(BaseModel):
    date: date
    seller_name: str
    seller_phone: Optional[str] = None
    pickup_location: Optional[str] = None
    transport_service: Optional[str] = None
    transport_cost: float = 0.0
    quantity: float
    unit: str = "kg"
    price_per_unit: float
    notes: Optional[str] = None


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseUpdate(BaseModel):
    date: Optional[Union[date, str]] = None
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    pickup_location: Optional[str] = None
    transport_service: Optional[str] = None
    transport_cost: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    notes: Optional[str] = None


class PurchaseResponse(PurchaseBase):
    id: int
    total_purchase_cost: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== SALE ITEM SCHEMAS ==============
class SaleItemBase(BaseModel):
    product_type_id: int
    quantity: float
    unit: str = "kg"
    price_per_unit: float


class SaleItemCreate(SaleItemBase):
    pass


class SaleItemResponse(SaleItemBase):
    id: int
    total_price: float
    product_type: Optional[ProductTypeResponse] = None

    class Config:
        from_attributes = True


# ============== SALE SCHEMAS ==============
class SaleBase(BaseModel):
    date: date
    buyer_id: int
    payment_type: PaymentType
    payment_received_now: float = 0.0
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    sale_items: List[SaleItemCreate]


class SaleUpdate(BaseModel):
    date: Optional[Union[date, str]] = None
    buyer_id: Optional[int] = None
    payment_type: Optional[PaymentType] = None
    payment_received_now: Optional[float] = None
    notes: Optional[str] = None


class SaleResponse(SaleBase):
    id: int
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime]
    buyer: BuyerResponse
    sale_items: List[SaleItemResponse]

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    id: int
    date: date
    buyer_name: str
    payment_type: PaymentType
    total_amount: float
    payment_received_now: float


# ============== PAYMENT SCHEMAS ==============
class PaymentBase(BaseModel):
    date: date
    buyer_id: int
    amount: float
    payment_method: str = "Cash"
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime
    buyer: Optional[BuyerResponse] = None

    class Config:
        from_attributes = True


# ============== EXPENSE SCHEMAS ==============
class ExpenseBase(BaseModel):
    date: date
    category: ExpenseCategory
    amount: float
    description: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    category: Optional[ExpenseCategory] = None
    amount: Optional[float] = None
    description: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== LEDGER SCHEMAS ==============
class LedgerEntry(BaseModel):
    date: date
    type: str  # "SALE", "PAYMENT"
    description: str
    debit: float
    credit: float
    balance: float


class BuyerLedgerResponse(BaseModel):
    buyer: BuyerResponse
    entries: List[LedgerEntry]
    opening_balance: float
    closing_balance: float


# ============== ANALYTICS SCHEMAS ==============
class DashboardSummary(BaseModel):
    today_purchases: float
    today_sales: float
    today_expenses: float
    total_purchases: float
    total_sales: float
    total_expenses: float
    total_profit: float
    total_receivable: float


class MonthlyStats(BaseModel):
    month: str
    purchases: float
    sales: float
    expenses: float
    profit: float


class ProductSalesStats(BaseModel):
    product_name: str
    total_quantity: float
    total_amount: float


class TopBuyerStats(BaseModel):
    buyer_name: str
    outstanding_amount: float


class AnalyticsResponse(BaseModel):
    monthly_stats: List[MonthlyStats]
    product_sales: List[ProductSalesStats]
    top_buyers: List[TopBuyerStats]


# ============== FILTER SCHEMAS ==============
class DateRangeFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PurchaseFilter(DateRangeFilter):
    seller_name: Optional[str] = None


class SaleFilter(DateRangeFilter):
    buyer_id: Optional[int] = None
    payment_type: Optional[PaymentType] = None


class ExpenseFilter(DateRangeFilter):
    category: Optional[ExpenseCategory] = None
