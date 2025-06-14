from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from model_folder.model import Payment, Staff
from database import SessionLocal
from typing import Annotated, Literal, List
from pydantic import BaseModel, Field
# from util.auth import get_current_user

#Dependecies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()
dbDepend = Annotated[Session, Depends(get_db)]
# userDepend = Annotated[Staff, Depends(get_current_user)]

# --- Pydantic Schemas ---
class PaymentCreate(BaseModel):
    other_details: str = Field(None, min_length=3, example="POS at front desk")
    payment_type: Literal["Cash", "Bank Transfer", "Card"] = Field(None, example="Card")

class PaymentResponse(BaseModel):
    bill_number: int
    other_details: str | None
    payment_type: str
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PaymentResponse, summary="Create new payment type")
async def add_payment_info(db: dbDepend, pay: PaymentCreate):
    """Add a new payment entry."""
    new_pay = Payment(**pay.model_dump(), is_active=True)
    db.add(new_pay)
    db.commit()
    db.refresh(new_pay)
    return new_pay

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[PaymentResponse], summary="Get all available payment types")
async def get_all_active_payments(db: dbDepend):
    """Retrieve all active (non-deleted) payments."""
    result =  db.query(Payment).filter(Payment.is_active == True).order_by(Payment.bill_number).all()
    return result

@router.get("/deleted", status_code=status.HTTP_200_OK, response_model=List[PaymentResponse], summary="Get all unavailable payment types")
async def get_all_inactive_payments(db: dbDepend):
    """Retrieve all inactive (soft-deleted) payments."""
    return db.query(Payment).filter(Payment.is_active == False).order_by(Payment.bill_number).all()

@router.get("/{pay_id}", status_code=status.HTTP_200_OK, response_model=PaymentResponse, summary="Get payment type by ID")
async def get_payment_by_id(db: dbDepend, pay_id: Annotated[int, Path(gt=0)]):
    """Retrieve a payment by its bill number."""
    pay = db.query(Payment).filter(Payment.bill_number == pay_id).first()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return pay

@router.put("/{pay_id}", status_code=status.HTTP_200_OK, response_model=PaymentResponse, summary="Update payment type")
async def update_payment_info(db: dbDepend, pay_id: Annotated[int, Path(gt=0)], pay_req: PaymentCreate):
    """Update payment info."""
    pay = db.query(Payment).filter(Payment.bill_number == pay_id).first()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    pay.other_details = pay_req.other_details
    pay.payment_type = pay_req.payment_type
    db.commit()
    db.refresh(pay)
    return pay

@router.patch("/{pay_id}/deactivate", status_code=status.HTTP_200_OK, response_model=PaymentResponse, summary="Deactivate payment type")
async def deactivate_payment(db: dbDepend, pay_id: Annotated[int, Path(gt=0)]):
    """Soft delete (deactivate) a payment."""
    pay = db.query(Payment).filter(Payment.bill_number == pay_id, Payment.is_active == True).first()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    pay.is_active = False
    db.commit()
    db.refresh(pay)
    return pay

@router.patch("/{pay_id}/reactivate", status_code=status.HTTP_200_OK, response_model=PaymentResponse, summary="Reactivate payment type")
async def reactivate_payment(db: dbDepend, pay_id: Annotated[int, Path(gt=0)]):
    """Reactivate a previously soft-deleted payment."""
    pay = db.query(Payment).filter(Payment.bill_number == pay_id, Payment.is_active == False).first()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    pay.is_active = True
    db.commit()
    db.refresh(pay)
    return pay
