from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal
from typing import Annotated, List, Optional
from model_folder.model import Order_Detail, Staff
from pydantic import BaseModel
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
class OrderDetailBase(BaseModel):
    order_id: int
    product_id: int
    bill_number: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    # total is calculated, not inputted

class Order_DetailOut(OrderDetailBase):
    id: int
    is_active: bool
    date: datetime
    total: float
    payment_name: Optional[str] = None  # display payment name instead of bill_number

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

# --- FastAPI Router ---

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderDetailBase, summary="Create new Order detail")
async def create_order_detail(order_req: OrderDetailBase, db: dbDepend, user: userDepend):
    """Create a new order_detail."""
    new_order = Order_Detail(**order_req.dict())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/active", status_code=status.HTTP_200_OK, response_model=List[Order_DetailOut], summary="Get all active Order details")
async def get_all_order_details(db: dbDepend, user: userDepend):
    """Get all active order_details."""
    result = db.query(Order_Detail).options(joinedload(Order_Detail.payment)).filter(Order_Detail.is_active == True).all()
    return [
        Order_DetailOut(
            **detail.__dict__,
            total=(detail.price or 0) * (1 - (detail.discount or 0) / 100),
            payment_name=detail.payment.name if detail.payment else None
        )
        for detail in result
    ]


@router.get("/inactive", status_code=status.HTTP_200_OK, response_model=List[Order_DetailOut], summary="Get all inactive Order details")
async def get_all_inactive_order_details(db: dbDepend, user: userDepend):
    """Get all inactive order_details."""
    result = db.query(Order_Detail).options(joinedload(Order_Detail.payment)).filter(Order_Detail.is_active == False).all()
    return [
        Order_DetailOut(
            **detail.__dict__,
            total=(detail.price or 0) * (1 - (detail.discount or 0) / 100),
            payment_name=detail.payment.name if detail.payment else None
        )
        for detail in result
    ]


@router.get("/{detail_id}", status_code=status.HTTP_200_OK, response_model=Order_DetailOut, summary="Get Order detail by id")
async def get_order_detail(detail_id: int, db: dbDepend, user: userDepend):
    """Get order_detail by id."""
    detail = db.query(Order_Detail).options(joinedload(Order_Detail.payment)).filter(Order_Detail.id == detail_id, Order_Detail.is_active == True).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Order_Detail not found")
    return Order_DetailOut(
        **detail.__dict__,
        total=(detail.price or 0) * (1 - (detail.discount or 0) / 100),
        payment_name=detail.payment.name if detail.payment else None
    )


@router.put("/{detail_id}", status_code=status.HTTP_200_OK, response_model=Order_DetailOut, summary="Update Order detail")
async def update_order_detail(detail_id: int, updated: OrderDetailBase, db: dbDepend, user: userDepend):
    """Update order_detail."""
    detail = db.query(Order_Detail).options(joinedload(Order_Detail.payment)).filter(Order_Detail.id == detail_id, Order_Detail.is_active == True).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Order_Detail not found")
    for key, value in updated.dict().items():
        setattr(detail, key, value)
    db.commit()
    db.refresh(detail)
    return Order_DetailOut(
        **detail.__dict__,
        total=(detail.price or 0) * (1 - (detail.discount or 0) / 100),
        payment_name=detail.payment.name if detail.payment else None
    )


@router.patch("/{detail_id}/deactivate", status_code=status.HTTP_200_OK, summary="Deactivate order_detail")
async def deactivate_order_detail(detail_id: int, db: dbDepend, user: userDepend):
    """Deactivate order_detail."""
    detail = db.query(Order_Detail).filter(Order_Detail.id == detail_id, Order_Detail.is_active == True).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Order_Detail not found")
    detail.is_active = False
    db.commit()
    return {"detail": "Order_Detail soft-deleted"}


@router.patch("/{detail_id}/reactivate", status_code=status.HTTP_200_OK, summary="Reactivate order_detail")
async def reactivate_order_detail(detail_id: int, db: dbDepend, user: userDepend):
    """Reactivate order_detail."""
    detail = db.query(Order_Detail).filter(Order_Detail.id == detail_id, Order_Detail.is_active == False).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Order_Detail not found")
    detail.is_active = True
    db.commit()
    db.refresh(detail)
    return {"detail": "Order_Detail reactivated"}


# Optional: Hard delete (disabled)
# @router.delete("/{detail_id}")
# async def hard_delete(db: dbDepend, detail_id: Annotated[int, Path(gt=0)]):
#     """Hard-delete product details including status."""
#     prod = db.query(Order_Detail).filter(Order_Detail.id == detail_id).first()
#     if not prod:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#     db.delete(prod)
#     db.commit()
#     return "prod"
