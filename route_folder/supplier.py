from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from model_folder.model import Supplier, Staff
from database import SessionLocal
from typing import List, Annotated
from util.auth import get_current_user

#Dependecies
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
class SupplierBase(BaseModel):
    name: Optional[str]
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class SupplierOut(SupplierBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SupplierOut, summary="Add new supplier" )
async def create_supplier(supplier: SupplierBase, db: dbDepend, user: userDepend):
    """Add a new suppler."""
    new_supplier = Supplier(**supplier.dict())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

@router.get("/", status_code=status.HTTP_200_OK,response_model=List[SupplierOut], summary="Get all active suppliers")
def get_active_suppliers(db: dbDepend, user: userDepend):
    """Retrieve all active (non-deleted) suppliers."""
    rows = db.query(Supplier).filter(Supplier.is_active == True).all()
    # Convert phone to string
    safe_rows = [
        SupplierOut.model_validate(
            {**row.__dict__, "phone": str(row.phone)}
        )
        for row in rows
    ]
    return safe_rows

@router.get("/inactive", status_code=status.HTTP_200_OK, response_model=List[SupplierOut], summary="Get all inactive suppliers")
def get_inactive_suppliers(db: dbDepend, user: userDepend):
    """Retrieve all inactive (soft-deleted) suppliers."""
    result = db.query(Supplier).filter(Supplier.is_active == False).all()
    return result

@router.get("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=SupplierOut, summary="Get supplier by ID")
def get_supplier(supplier_id: int, db: dbDepend, user: userDepend):
    """Retrieve a supplier by ID."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == True).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.put("/{supplier_id}", response_model=SupplierOut, status_code=status.HTTP_200_OK, summary="Update supplier info")
def update_supplier(supplier_id: int, updated: SupplierBase, db: dbDepend, user: userDepend):
    """Update supplier info"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == True).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for key, value in updated.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    db.commit()
    db.refresh(supplier)
    return supplier

@router.patch("/{supplier_id}/deactivate", status_code=status.HTTP_200_OK, response_model=SupplierOut, summary="Deactivate supplier")
def deactivate_supplier(supplier_id: int, db: dbDepend, user: userDepend):
    """Soft delete (deactivate) a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == True).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = False
    db.commit()
    return {"message": f"Supplier {supplier_id} deactivated."}

@router.patch("/{supplier_id}/reactivate", status_code=status.HTTP_200_OK, response_model=SupplierOut, summary="Reactivate supplier")
def reactivate_supplier(supplier_id: int, db: dbDepend, user: userDepend):
    """Reactivate a previously soft-deleted supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_active == False).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = True
    db.commit()
    return {"message": f"Supplier {supplier_id} reactivated."}
