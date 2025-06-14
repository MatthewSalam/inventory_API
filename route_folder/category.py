from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, joinedload
from model_folder.model import Category, Staff
from database import SessionLocal
from typing import Annotated, List
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
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=3)
    description: str = Field(..., min_length=3)

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    product_count: int

    class Config:
        from_attributes = True


# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse, summary="Create new category")
async def create_category(db: dbDepend, cate: CategoryCreate):
    """Add a new category entry."""
    new_cate = Category(**cate.dict(), is_active=True)
    db.add(new_cate)
    db.commit()
    db.refresh(new_cate)
    return CategoryResponse(
        id=new_cate.id,
        name=new_cate.name,
        description=new_cate.description,
        is_active=new_cate.is_active,
        product_count=len(new_cate.products)
    )

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[CategoryResponse], summary="All active categories")
async def get_all_active_categories(db: dbDepend):
    """Retrieve all active (non-deleted) categories."""
    categories = db.query(Category).options(joinedload(Category.products)).filter(Category.is_active == True).order_by(Category.id).all()
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            is_active=c.is_active,
            product_count=len(c.products)
        )
        for c in categories
    ]

@router.get("/deleted", status_code=status.HTTP_200_OK, response_model=List[CategoryResponse],summary="All inactive category")
async def get_all_inactive_categories(db: dbDepend):
    """Retrieve all inactive (soft-deleted) categories."""
    categories = db.query(Category).options(joinedload(Category.products)).filter(Category.is_active == False).order_by(Category.id).all()
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            is_active=c.is_active,
            product_count=len(c.products)
        )
        for c in categories
    ]

@router.get("/{cate_id}", status_code=status.HTTP_200_OK, response_model=CategoryResponse, summary="Get category by id")
async def get_category_by_id(db: dbDepend, cate_id: Annotated[int, Path(gt=0)]):
    """Retrieve a category by its ID."""
    category = db.query(Category).options(joinedload(Category.products)).filter(Category.id == cate_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        product_count=len(category.products)
    )

@router.put("/{cate_id}", status_code=status.HTTP_200_OK, response_model=CategoryResponse, summary="Update category")
async def update_category(db: dbDepend, cate_id: Annotated[int, Path(..., gt=0)], cate_req: CategoryCreate):
    """Update a Category."""
    cat = db.query(Category).filter(Category.id == cate_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category does not exist")
    cat.name = cate_req.name
    cat.description = cate_req.description
    db.commit()
    db.refresh(cat)
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        is_active=cat.is_active,
        product_count=len(cat.products)
    )

@router.patch("/{cate_id}/deactivate", status_code=status.HTTP_200_OK, response_model=CategoryResponse, summary="Deactivate category")
async def deactivate_category(db: dbDepend, cate_id: Annotated[int, Path(gt=0)]):
    """Soft delete (deactivate) a category."""
    cat = db.query(Category).filter(Category.id == cate_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category does not exist")
    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        is_active=cat.is_active,
        product_count=len(cat.products)
    )

@router.patch("/{cate_id}/reactivate", status_code=status.HTTP_200_OK, response_model=CategoryResponse, summary="Reactivate category")
async def reactivate_category(db: dbDepend, cate_id: Annotated[int, Path(gt=0)]):
    """Reactivate a previously soft-deleted category."""
    cat = db.query(Category).filter(Category.id == cate_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category does not exist")
    cat.is_active = True
    db.commit()
    db.refresh(cat)
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        is_active=cat.is_active,
        product_count=len(cat.products)
    )
