from fastapi import APIRouter, Depends, HTTPException
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
                         page: int = 1,
                         page_size: int = 10
                         ):
    query = db.query(Category)
    offset = (page - 1) * page_size

    return db.query(Category).offset(offset).limit(page_size).all()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def create_category(db: db_dependency, category: CategoryCreate):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
