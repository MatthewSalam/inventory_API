from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from model_folder.model import Order, Staff
from database import SessionLocal
from typing import Annotated, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from util.auth import get_current_user


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()
dbDepend = Annotated[Session, Depends(get_db)]
userDepend = Annotated[Staff, Depends(get_current_user)]

# --- Pydantic Schemas ---
class OrderCreate(BaseModel):
    customer_id: Optional[int] = None
    detail: Optional[str] = None

class OrderResponse(OrderCreate):
    id: int
    order_date: datetime
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, summary="Add new order")
async def add_order(db: dbDepend, orde: OrderCreate, user: userDepend):
    """Add a new order."""
    new_order = Order(**orde.dict())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/active", status_code=status.HTTP_200_OK, summary="Get all active orders")
async def get_all_active_orders(db: dbDepend, user: userDepend):
    """Get all active orders."""
    orders = db.query(Order).filter(Order.is_active == True).order_by(Order.id).all()
    return orders

@router.get("/inactive", status_code=status.HTTP_200_OK, summary="Get all inactive orders")
async def get_inactive_orders(db: dbDepend, user: userDepend):
    """Get all inactive orders."""
    orders = db.query(Order).filter(Order.is_active == False).order_by(Order.id).all()
    return orders

@router.get("/{order_id}", status_code=status.HTTP_200_OK, summary="Get order by ID")
async def get_order_by_id(db: dbDepend, order_id: Annotated[int, Path(..., gt=0)], user: userDepend):
    """Get order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        return order
    raise HTTPException(status_code=404, detail="Order not found")

@router.put("/{order_id}", status_code=status.HTTP_200_OK, summary="Update order")
async def update_order(db: dbDepend, order_id: Annotated[int, Path(..., gt=0)],    order_req: OrderCreate, user: userDepend):
    """Update order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order does not exist")
    for field, value in order_req.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return {"message": "Order updated successfully"}

@router.patch("/{order_id}", status_code=status.HTTP_200_OK, summary="Deactivate orders")
async def deactivate_order(db: dbDepend, order_id: Annotated[int, Path(..., gt=0)], user: userDepend):
    """Deactivate order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.is_active = False
    db.commit()
    return {"message": "Order deactivated successfully"}

@router.patch("/{order_id}/reactivate", status_code=status.HTTP_200_OK, summary="Activate orders")
async def reactivate_order(db: dbDepend, order_id: Annotated[int, Path(..., gt=0)], user: userDepend):
    """Reactivate order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.is_active = True
    db.commit()
    return {"message": "Order reactivated successfully"}
