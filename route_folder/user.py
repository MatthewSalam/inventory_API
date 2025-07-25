from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, joinedload
from model_folder.model import User, Staff
from database import SessionLocal
from typing import Annotated, List
from pydantic import BaseModel, Field, EmailStr
from util.auth import get_current_user


#Dependecies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()
dbDependency = Annotated[Session, Depends(get_db)]
userDepend = Annotated[Staff, Depends(get_current_user)]


# --- Pydantic Schemas ---

class UserCreate(BaseModel):
    lastname: str = Field(..., min_length=1, example="Doe")
    firstname: str = Field(..., min_length=1, example="Jane")
    email: EmailStr = Field(..., example="jane.doe@example.com")
    phone: str = Field(..., min_length=7, max_length=15, example="+1234567890")
    staff_id: int | None = Field(None, example=1)

class UserUpdate(BaseModel):
    lastname: str 
    firstname: str 
    email: EmailStr 
    phone: str 
class UserResponse(BaseModel):
    id: int
    lastname: str
    firstname: str
    email: EmailStr
    phone: str
    staff_id: int | None
    is_active: bool

    class Config:
        from_attributes = True

# --- FastAPI Router ---

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse, summary="Register new user")
async def create_user(db: dbDependency, cust: UserCreate, user: userDepend):
    """Register a new user with the system."""
    new_user = User(**cust.model_dump(), is_active=True)  # Active by default
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", status_code=status.HTTP_200_OK, summary="Get all active users")
async def get_all_active_users(db: dbDependency, user: userDepend):
    """Retrieve a list of all active users"""
    users = db.query(User).options(joinedload(User.staff)).filter(User.is_active == True).order_by(User.id).all()
    return [
        {
            "id": user.id,
            "lastname": user.lastname,
            "firstname": user.firstname,
            "email": user.email,
            "phone": user.phone,
            "Staff assigned": user.staff.username if user.staff else None
        }
        for user in users
    ]

@router.get("/inactive", status_code=status.HTTP_200_OK, response_model=List[UserResponse], summary="Get all inactive users")
async def get_all_inactive_users(db: dbDependency, user: userDepend):
    """Retrieve a list of all inactive (soft-deleted) users."""
    return db.query(User).filter(User.is_active == False).order_by(User.id).all()

@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse, summary="Get user by ID")
async def get_user_by_id(db: dbDependency, user_id: Annotated[int, Path(gt=0, example=1)], user: userDepend):
    """Retrieve a user by their ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse, summary="Update user")
async def update_user(db: dbDependency, cust_req: UserUpdate, user_id: Annotated[int, Path(gt=0)], user: userDepend):
    """Update user details."""
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in cust_req.model_dump(exclude_unset=True).items():
        setattr(user_obj, field, value)
    db.commit()
    db.refresh(user_obj)
    return user_obj


@router.patch("/{user_id}/deactivate", status_code=status.HTTP_200_OK, response_model=UserResponse, summary="Deactivate user")
async def deactivate_user(db: dbDependency, user_id: Annotated[int, Path(gt=0)], user: userDepend):
    """Soft-delete a user by setting is_active to False."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}/reactivate", status_code=status.HTTP_200_OK, response_model=UserResponse, summary="Reactivate user")
async def reactivate_user(db: dbDependency, user_id: Annotated[int, Path(gt=0)], user: userDepend):
    """Reactivate a previously deactivated user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user
