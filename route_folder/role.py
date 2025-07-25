from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from model_folder.model import Role, Staff
from database import SessionLocal
from util.auth import get_current_user

#Dependecies 
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

dbDepend = Annotated[Session, Depends(get_db)]
userdepend = Annotated[Staff, Depends(get_current_user)]

# --- Pydantic Schemas ---
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, example="Manager")
    description: str | None = Field(None, example="Handles staff and operations")

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleCreate):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True
class RoleWithCount(RoleResponse):
    staff_count: int


# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create new role")
async def create_role(db: dbDepend, role: RoleCreate, user: userdepend):
    """Add a new role."""
    new_role = Role(**role.model_dump(), is_active=True)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[RoleWithCount], summary="Get all active roles")
async def get_roles(db: dbDepend, user: userdepend):#
    """Retrieve all active (non-deleted) payments."""
    roles = (db.query(Role).options(joinedload(Role.staff)).filter(Role.is_active == True).all())
    
    result = []
    for role in roles:
        count = sum(1 for staff in role.staff if staff.is_active)
        role_data = RoleWithCount(**role.__dict__, staff_count=count)
        result.append(role_data)
    
    return result

@router.get("/inactive", status_code=status.HTTP_200_OK, response_model=List[RoleWithCount], summary="All inactive roles")
async def get_inactive_roles(db: dbDepend, user: userdepend):#
    """Retrieve all inactive (soft-deleted) roles."""
    roles = db.query(Role).options(joinedload(Role.staff)).filter(Role.is_active == False).all()

    result = []
    for role in roles:
        count = sum(1 for staff in role.staff if staff.is_active)
        result.append(RoleWithCount(**role.__dict__, staff_count=count))

    return result

@router.get("/{role_id}", status_code=status.HTTP_200_OK, summary="Get role by ID")
async def get_role_by_id(db: dbDepend, role_id: Annotated[int, Path(..., gt=0)], user: userdepend):#
    """Retrieve a role by its ID."""
    role = db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role

@router.patch("/{role_id}", status_code=status.HTTP_200_OK,summary="Update role")
async def update_role(db: dbDepend, role_id: Annotated[int, Path(..., gt=0)], role_req: RoleUpdate, user: userdepend):#
    """Update role info."""
    role = db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    for field, value in role_req.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role

@router.patch("/{role_id}/deactivate", status_code=status.HTTP_200_OK,summary="Deactivate role")
async def deactivate_role(db: dbDepend, role_id: Annotated[int, Path(..., gt=0)], user: userdepend):#
    """Soft delete (deactivate) a role."""
    role = db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role.is_active = False
    db.commit()
    db.refresh(role)
    return "Deactivated successfully"

@router.patch("/{role_id}/reactivate", status_code=status.HTTP_200_OK, summary="Reactivate role")
async def reactivate_role(db: dbDepend, role_id: Annotated[int, Path(..., gt=0)], user: userdepend):#
    """Reactivate a previously soft-deleted role."""
    role = db.query(Role).filter(Role.id == role_id, Role.is_active == False).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role.is_active = True
    db.commit()
    db.refresh(role)
    return "Successful"
