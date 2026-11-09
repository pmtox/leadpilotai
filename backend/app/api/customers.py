from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.models.customer import Customer
from backend.app.schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.post("", response_model=CustomerResponse)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(
        name=customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        preferred_language=customer_in.preferred_language
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("", response_model=List[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.id.desc()).all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
