from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from model_folder.model import Staff
from database import SessionLocal
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, EmailStr
from util.security import hash_password
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

class StaffCreate(BaseModel):
    lastname: str = Field(..., min_length=1, example="Doe")
    firstname: str = Field(..., min_length=1, example="John")
    username: str = Field(..., min_length=2, example="johndoe")
    password: str = Field(..., min_length=5, example="secure123")
    address: str = Field(..., min_length=5, example="123 Main St")
    email: EmailStr = Field(..., example="john.doe@example.com")
    phone: str = Field(..., min_length=7, example="+1234567890")
    role_id: int = Field(..., gt=0, example=1)

class StaffUpdate(BaseModel):
    lastname: Optional[str] = Field(None, min_length=1, example="Doe")
    firstname: Optional[str] = Field(None, min_length=1, example="John")
    username: Optional[str] = Field(None, min_length=2, example="johndoe")
    password: Optional[str] = Field(None, min_length=5, example="secure123")
    address: Optional[str] = Field(None, min_length=5, example="123 Main St")
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    phone: Optional[str] = Field(None, min_length=7, example="+1234567890")
    role_id: Optional[int] = Field(None, gt=0, example=1)

class StaffResponse(StaffCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Router ---
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=StaffResponse, summary="Register new staff member")
async def create_staff_member(db: dbDepend, staff: StaffCreate): #user: userDepend):
    """Register a new staff member with the system."""
    existing_staff = db.query(Staff).filter((Staff.username == staff.username) | (Staff.email == staff.email)).first()
    if existing_staff:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,  detail="Username or email already exists")
    hashed = hash_password(staff.password)
    new_staff = Staff(**staff.model_dump(exclude={"password"}), password=hashed, is_active=True)# New staff are active by default)
                      
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[StaffResponse], summary="Get all active staff members")
async def get_active_staff(db: dbDepend): #user: userDepend):
    """Retrieve a list of all active staff members."""
    result = db.query(Staff).filter(Staff.is_active == True).order_by(Staff.id).all()
    return result

@router.get("/deleted", status_code=status.HTTP_200_OK, response_model=List[StaffResponse], summary="Get all inactive staff members")
async def get_inactive_staff(db: dbDepend, user: userDepend):#
    """Retrieve a list of all inactive (deleted) staff members."""
    result = db.query(Staff).filter(Staff.is_active == False).order_by(Staff.id).all()
    return result

@router.get("/{staff_id}", status_code=status.HTTP_200_OK, response_model=StaffResponse, summary="Get staff by ID")
async def get_staff_by_id(db: dbDepend, staff_id: Annotated[int, Path(..., gt=0, example=1)], user: userDepend):#
    """Retrieve a specific staff member by their ID."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return staff

@router.put("/{staff_id}", status_code=status.HTTP_200_OK, response_model=StaffResponse, summary="Update staff member")
async def update_staff(db: dbDepend, staff_id: Annotated[int, Path(..., gt=0)], staff_req: StaffUpdate, user: userDepend):
    """Update a staff member's details."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    update_data = staff_req.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
    for field, value in update_data.items():
        setattr(staff, field, value)
    db.commit()
    db.refresh(staff)
    return staff

@router.patch("/{staff_id}/deactivate", status_code=status.HTTP_200_OK, response_model=StaffResponse, summary="Deactivate staff member")
async def deactivate_staff(db: dbDepend, staff_id: Annotated[int, Path(..., gt=0)], user: userDepend):#
    """Deactivate a staff member (mark as deleted)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    staff.is_active = False
    db.commit()
    db.refresh(staff)
    return staff

@router.patch("/{staff_id}/reactivate", status_code=status.HTTP_200_OK, response_model=StaffResponse, summary="Reactivate staff member")
async def reactivate_staff(db: dbDepend, staff_id: Annotated[int, Path(..., gt=0)], user: userDepend):#
    """Reactivate a previously deactivated staff member."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    staff.is_active = True
    db.commit()
    db.refresh(staff)
    return staff