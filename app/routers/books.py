from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Book, BookAuthor
from app.schemas import BookCreate, BookResponse

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/books", tags=["books"])
db_dependency = Annotated[Session, Depends(get_db)]

# GET / books(filter: category_id, author_id, available) #check
# GET / books/{id} #check
# POST / books #check
# PUT / books/{id} #check
# DELETE / books/{id} # check
# GET    / books/{id}/authors


@router.get("/", response_model=list[BookResponse])
async def get_books(db: db_dependency,
                    category_id: int | None = None,
                    author_id: int | None = None,
                    available: bool | None = None):
    query = db.query(Book)
    # Filtrimi 1
    if category_id is not None:
        query = query.filter(Book.category_id == category_id)

    # Filtrimi 2
    # Duhet join per shkak se nuk kemi direkt qasje ne tabelen BookAuthor (per ta marr  author_id)
    if author_id is not None:
        query = query.join(BookAuthor).filter(
            BookAuthor.author_id == author_id)

    # Filtrimi 3
    if available is not None:
        if available:
            query = query.filter(Book.total_copies > 0)
        else:
            query = query.filter(Book.total_copies == 0)

    return query.all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(db: db_dependency,
                   book_id: int
                   ):
    book_exists = db.query(Book).filter(Book.id == book_id).first()

    if not book_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky liber nuk ekziston!"
        )

    return book_exists


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(db: db_dependency, book: BookCreate):
    dupe_isbn = db.query(Book).filter(Book.isbn == book.isbn).first()

    if dupe_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Libri me kete isbn ekziston"
        )

    db_book = Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(db: db_dependency, book_id: int, book: BookCreate):
    book_exist = db.query(Book).filter(Book.id == book_id).first()

    if not book_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri me kete id nuk ekzistion"
        )

    book_exist.title = book.title
    book_exist.isbn = book.isbn
    book_exist.category_id = book.category_id
    book_exist.total_copies = book.total_copies
    book_exist.published_year = book.published_year

    db.commit()
    db.refresh(book_exist)
    return book_exist


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(db: db_dependency, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky liber nuk gjendet ne librari!"
        )

    db.delete(book)
    db.commit()
