# Kastbhanjan Playwood Management System - Backend

FastAPI-based backend for the wooden scrap trading business management system.

## Features

- JWT Authentication with secure password hashing
- PostgreSQL database with SQLAlchemy ORM
- RESTful API for all modules
- Comprehensive business logic for scrap trading

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT with python-jose
- **Password Hashing**: passlib with bcrypt

## Project Structure

```
kastbhanjan-backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── auth.py              # Authentication utilities
├── seed_data.py         # Database seeding
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── routers/
    ├── auth.py          # Authentication routes
    ├── purchases.py     # Purchase management
    ├── sales.py         # Sales management
    ├── buyers.py        # Customer/Khata management
    ├── expenses.py      # Expense tracking
    ├── product_types.py # Product type management
    └── analytics.py     # Analytics and reporting
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd kastbhanjan-backend
pip install -r requirements.txt
```

### 2. Configure Database

Create a PostgreSQL database:

```bash
createdb kastbhanjan
```

Update `.env` file with your database credentials:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/kastbhanjan
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 3. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Default Login Credentials

- **Email**: admin@kastbhanjan.com
- **Password**: admin123

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Purchases
- `GET /api/purchases` - List purchases
- `POST /api/purchases` - Create purchase
- `GET /api/purchases/{id}` - Get purchase
- `PUT /api/purchases/{id}` - Update purchase
- `DELETE /api/purchases/{id}` - Delete purchase

### Sales
- `GET /api/sales` - List sales
- `POST /api/sales` - Create sale
- `GET /api/sales/{id}` - Get sale
- `PUT /api/sales/{id}` - Update sale
- `DELETE /api/sales/{id}` - Delete sale

### Buyers (Customers)
- `GET /api/buyers` - List buyers
- `POST /api/buyers` - Create buyer
- `GET /api/buyers/{id}` - Get buyer
- `PUT /api/buyers/{id}` - Update buyer
- `DELETE /api/buyers/{id}` - Delete buyer
- `GET /api/buyers/{id}/ledger` - Get buyer ledger (Khata)
- `POST /api/buyers/{id}/payments` - Add payment

### Expenses
- `GET /api/expenses` - List expenses
- `POST /api/expenses` - Create expense
- `GET /api/expenses/{id}` - Get expense
- `PUT /api/expenses/{id}` - Update expense
- `DELETE /api/expenses/{id}` - Delete expense

### Analytics
- `GET /api/analytics/dashboard-summary` - Dashboard summary
- `GET /api/analytics/monthly-stats` - Monthly statistics
- `GET /api/analytics/product-sales` - Sales by product
- `GET /api/analytics/top-buyers` - Top buyers by outstanding

## Database Schema

### Tables

1. **users** - Admin users
2. **buyers** - Customer information
3. **product_types** - Master product types (Ply, Lafa, Jalav, etc.)
4. **purchases** - Scrap purchase records
5. **sales** - Sale transactions
6. **sale_items** - Individual items in a sale
7. **payments** - Customer payments
8. **expenses** - Business expenses

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/kastbhanjan` |
| `SECRET_KEY` | JWT secret key | `your-secret-key` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## License

MIT License