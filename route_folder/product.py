from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, joinedload
from model_folder.model import Product, Staff
from database import SessionLocal
from typing import Annotated, Literal, List
from pydantic import BaseModel, Field
# from util.auth import get_current_user

# Dependencies
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
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=3)
    desc: str = Field(..., min_length=10)
    unit: int = Field(..., example=100)
    other_details: str | None = Field(None)
    price: float = Field(..., example=19.99)
    cat_id: int = Field(..., example=1)
    supplier_id: int = Field(..., example=1)

class ProductUpdate(ProductCreate):
    status: Literal["Available", "Unavailable"] = Field(...)

class ProductResponse(BaseModel):
    id: int
    name: str
    desc: str
    unit: int
    other_details: str | None
    price: float
    supplier_id: int
    status: str
    category_name: str

    class Config:
        from_attributes = True

# --- FastAPI Router ---
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse, summary="Create new product")
async def create_product(db: dbDepend, prod: ProductCreate):
    """Add a new product with default status 'Available'."""
    new_prod = Product(**prod.model_dump(), status="Available")
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return {
        **new_prod.__dict__,
        "category_name": new_prod.category.name
    }

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProductResponse], summary="Get all available products")
async def get_all_available_products(db: dbDepend):
    """Retrieve all available products."""
    products = db.query(Product).options(joinedload(Product.category)).filter(Product.status == "Available").order_by(Product.id).all()
    return [
        {**prod.__dict__, "category_name": prod.category.name}
        for prod in products
    ]

@router.get("/unavailable", status_code=status.HTTP_200_OK, response_model=List[ProductResponse], summary="Get all unavailable products")
async def get_all_unavailable_products(db: dbDepend):
    """Retrieve all unavailable products."""
    products = db.query(Product).options(joinedload(Product.category)).filter(Product.status == "Unavailable").order_by(Product.id).all()
    return [
        {**prod.__dict__, "category_name": prod.category.name}
        for prod in products
    ]

@router.get("/{prod_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse, summary="Get product by ID")
async def get_product_by_id(db: dbDepend, prod_id: Annotated[int, Path(gt=0)]):
    """Retrieve a product by its ID."""
    prod = db.query(Product).options(joinedload(Product.category)).filter(Product.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {
        **prod.__dict__,
        "category_name": prod.category.name
    }

@router.put("/{prod_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse, summary="Update product")
async def update_product(db: dbDepend, prod_id: Annotated[int, Path(gt=0)], prod_req: ProductUpdate):
    """Update product details including status."""
    prod = db.query(Product).options(joinedload(Product.category)).filter(Product.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for field, value in prod_req.model_dump().items():
        setattr(prod, field, value)
    db.commit()
    db.refresh(prod)
    return {
        **prod.__dict__,
        "category_name": prod.category.name
    }

@router.patch("/{prod_id}/deactivate", status_code=status.HTTP_200_OK, response_model=ProductResponse, summary="Deactivate product")
async def deactivate_product(db: dbDepend, prod_id: Annotated[int, Path(gt=0)]):
    """Mark a product as Unavailable."""
    prod = db.query(Product).options(joinedload(Product.category)).filter(Product.id == prod_id, Product.status == "Available").first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    prod.status = "Unavailable"
    db.commit()
    db.refresh(prod)
    return {
        **prod.__dict__,
        "category_name": prod.category.name
    }

@router.patch("/{prod_id}/reactivate", status_code=status.HTTP_200_OK, response_model=ProductResponse, summary="Reactivate product")
async def reactivate_product(db: dbDepend, prod_id: Annotated[int, Path(gt=0)]):
    """Mark a previously unavailable product as Available."""
    prod = db.query(Product).options(joinedload(Product.category)).filter(Product.id == prod_id, Product.status == "Unavailable").first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    prod.status = "Available"
    db.commit()
    db.refresh(prod)
    return {
        **prod.__dict__,
        "category_name": prod.category.name
    }


# @router.delete("/{prod_id}")
# async def hard_delete(db: dbDepend, prod_id: Annotated[int, Path(gt=0)]):
#     """Hard-delete product details including status."""
#     prod = db.query(Product).filter(Product.id == prod_id).first()
#     if not prod:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
#     db.delete(prod)
#     db.commit()
#     return prod