from sqlalchemy.orm import Session
import models
from auth import get_password_hash

def seed_product_types(db: Session):
    """Seed default product types"""
    default_products = [
        {"name": "Ply", "description": "Plywood sheets"},
        {"name": "Lafa", "description": "Lafa wood pieces"},
        {"name": "Jalav", "description": "Jalav wood"},
        {"name": "Sheet", "description": "Wood sheets"},
        {"name": "Chavi", "description": "Chavi wood"},
        {"name": "Khili", "description": "Khili wood pieces"},
    ]
    
    for product_data in default_products:
        existing = db.query(models.ProductType).filter(
            models.ProductType.name == product_data["name"]
        ).first()
        if not existing:
            product = models.ProductType(**product_data)
            db.add(product)
    
    db.commit()
    print("Product types seeded successfully")

def seed_admin_user(db: Session):
    """Seed default admin user"""
    admin = db.query(models.User).filter(
        models.User.email == "admin@kastbhanjan.com"
    ).first()
    
    if not admin:
        admin = models.User(
            email="admin@kastbhanjan.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Kastbhanjan Admin",
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Default admin user created: admin@kastbhanjan.com / admin123")

def seed_all_data(db: Session):
    """Run all seed operations"""
    seed_product_types(db)
    seed_admin_user(db)
    print("Database seeding completed!")