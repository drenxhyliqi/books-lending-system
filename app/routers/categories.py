from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse
from app.auth import verify_api_key

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/categories", tags=["categories"])
db_dependency = Annotated[Session, Depends(get_db)]


# GET    / categories
# POST / categories

@router.get("/", response_model=list[CategoryResponse])
async def get_categories(db: db_dependency,
                         page: int = Query(1, ge=1),
                         page_size: int = Query(10, ge=1)
                         ):
    offset = (page - 1) * page_size

    return db.query(Category).order_by(Category.id).offset(offset).limit(page_size).all()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def create_category(db: db_dependency, category: CategoryCreate):
    name_exist = db.query(Category).filter(
        Category.name == category.name).first()

    if name_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kjo kategori tashme ekziston"
        )

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
