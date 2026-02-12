from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, purchases, sales, buyers, expenses, product_types, analytics
from seed_data import seed_all_data
from sqlalchemy.orm import Session
from database import SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed initial data
db = SessionLocal()
try:
    seed_all_data(db)
finally:
    db.close()

app = FastAPI(
    title="Kastbhanjan Playwood Management System",
    description="API for wooden scrap trading business management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(purchases.router)
app.include_router(sales.router)
app.include_router(buyers.router)
app.include_router(expenses.router)
app.include_router(product_types.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {
        "message": "Kastbhanjan Playwood Management System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
