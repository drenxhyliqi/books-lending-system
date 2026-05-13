from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Author
from app.schemas import AuthorCreate, AuthorResponse

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/authors", tags=["authors"])
db_dependency = Annotated[Session, Depends(get_db)]


# GET / authors
# GET / authors/{id}
# POST / authors

@router.get("/", response_model=list[AuthorResponse])
async def get_authors(db: db_dependency):
    query = db.query(Author)

    return query.all()


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(db: db_dependency, author_id: int):
    author_exist = db.query(Author).filter(Author.id == author_id).first()

    if not author_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky autor nuk ekziston"
        )

    return author_exist


@router.post("/", response_model=AuthorResponse)
async def create_author(db: db_dependency,
                        author: AuthorCreate
                        ):

    db_author = Author(**author.model_dump())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author
