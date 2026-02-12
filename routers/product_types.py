from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/product-types", tags=["Product Types"])

@router.get("", response_model=List[schemas.ProductTypeResponse])
def get_product_types(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all product types"""
    product_types = db.query(models.ProductType).order_by(models.ProductType.name).all()
    return product_types

@router.get("/{product_type_id}", response_model=schemas.ProductTypeResponse)
def get_product_type(
    product_type_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get a single product type by ID"""
    product_type = db.query(models.ProductType).filter(
        models.ProductType.id == product_type_id
    ).first()
    if not product_type:
        raise HTTPException(status_code=404, detail="Product type not found")
    return product_type

@router.post("", response_model=schemas.ProductTypeResponse, status_code=201)
def create_product_type(
    product_type: schemas.ProductTypeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new product type"""
    # Check if name already exists
    existing = db.query(models.ProductType).filter(
        models.ProductType.name == product_type.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product type already exists")
    
    db_product_type = models.ProductType(**product_type.dict())
    db.add(db_product_type)
    db.commit()
    db.refresh(db_product_type)
    return db_product_type

@router.put("/{product_type_id}", response_model=schemas.ProductTypeResponse)
def update_product_type(
    product_type_id: int,
    product_type_update: schemas.ProductTypeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a product type"""
    db_product_type = db.query(models.ProductType).filter(
        models.ProductType.id == product_type_id
    ).first()
    if not db_product_type:
        raise HTTPException(status_code=404, detail="Product type not found")
    
    # Check if new name conflicts with another product
    if product_type_update.name != db_product_type.name:
        existing = db.query(models.ProductType).filter(
            models.ProductType.name == product_type_update.name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product type name already exists")
    
    db_product_type.name = product_type_update.name
    db_product_type.description = product_type_update.description
    
    db.commit()
    db.refresh(db_product_type)
    return db_product_type

@router.delete("/{product_type_id}")
def delete_product_type(
    product_type_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a product type"""
    db_product_type = db.query(models.ProductType).filter(
        models.ProductType.id == product_type_id
    ).first()
    if not db_product_type:
        raise HTTPException(status_code=404, detail="Product type not found")
    
    # Check if product type is used in sales
    if db_product_type.sale_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product type that is used in sales"
        )
    
    db.delete(db_product_type)
    db.commit()
    return {"message": "Product type deleted successfully"}