from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Author, Book, BookAuthor, Category, Loan
from app.schemas import AuthorResponse, BookCreate, BookResponse, LoanResponse
from app.auth import verify_api_key

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/books", tags=["books"])
db_dependency = Annotated[Session, Depends(get_db)]

# GET / books(filter: category_id, author_id, available) #check
# GET / books/{id} #check
# POST / books #check
# PUT / books/{id} #check
# DELETE / books/{id} # check
# GET    / books/{id}/authors
# GET    / books/{id}/loan-history
# POST   / books/{id}/authors/{author_id}
# DELETE / books/{id}/authors/{author_id}


# Numri i huazimeve aktive per librin, e perdorin filtrat available
# Liber i lire = total_copies eshte me i madh se huazimet aktive
def active_loans_count(db):
    return db.query(func.count(Loan.id)).filter(
        Loan.book_id == Book.id,
        Loan.return_date == None
    ).correlate(Book).scalar_subquery()


@router.get("/", response_model=list[BookResponse])
async def get_books(db: db_dependency,
                    category_id: int | None = None,
                    author_id: int | None = None,
                    available: bool | None = None,
                    page: int = Query(1, ge=1),
                    page_size: int = Query(30, ge=1)
                    ):
    query = db.query(Book)
    offset = (page - 1) * page_size
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
            query = query.filter(Book.total_copies > active_loans_count(db))
        else:
            query = query.filter(Book.total_copies <= active_loans_count(db))

    # Pa order_by radhitja mes faqeve nuk eshte e garantuar
    return query.order_by(Book.id).offset(offset).limit(page_size).all()


@router.get("/search")
async def search_books(
    db: db_dependency,
    q: str | None = None,
    category_id: int | None = None,
    author_id: int | None = None,
    available_only: bool | None = None,
    published_after: int | None = None,
    published_before: int | None = None,
    sort_by: str = 'title',
    order_by: str = 'asc',
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1)
):
    query = db.query(Book).options(joinedload(Book.authors))

    # Filtrimet
    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))

    if category_id:
        query = query.filter(Book.category_id == category_id)

    if author_id:
        query = query.join(BookAuthor).filter(
            BookAuthor.author_id == author_id)

    if available_only:
        query = query.filter(Book.total_copies > active_loans_count(db))

    if published_after:
        query = query.filter(Book.published_year >=
                             date(published_after, 1, 1))

    if published_before:
        query = query.filter(Book.published_year <=
                             date(published_before, 12, 31))

    # Sortimi
    if sort_by == 'title':
        order = Book.title.asc() if order_by == "asc" else Book.title.desc()
    elif sort_by == "published_year":
        order = Book.published_year.asc() if order_by == "asc" else Book.published_year.desc()
    elif sort_by == "popularity":
        query = query.outerjoin(Loan).group_by(Book.id)
        order = func.count(Loan.id).asc(
        ) if order_by == "asc" else func.count(Loan.id).desc()
    else:
        order = Book.title.asc()

    query = query.order_by(order)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    # Pagination
    books = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": books,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }


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


@router.get("/{book_id}/authors", response_model=list[AuthorResponse])
async def get_book_authors(db: db_dependency, book_id: int):
    books = db.query(Book).filter(Book.id == book_id).first()

    if not books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri nuk gjendet!"
        )

    return books.authors


@router.get("/{book_id}/loan-history", response_model=list[LoanResponse])
async def get_book_loan_history(db: db_dependency, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri nuk gjendet!"
        )

    return book.loans  # SELECT * FROM loans WHERE book_id = 1


@router.post("/{book_id}/authors/{author_id}", response_model=list[AuthorResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def add_book_author(db: db_dependency, book_id: int, author_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri nuk gjendet!"
        )

    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky autor nuk ekziston"
        )

    if author in book.authors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ky autor eshte tashme i lidhur me kete liber"
        )

    # SQLAlchemy e shton vete rreshtin ne tabelen book_authors
    book.authors.append(author)
    db.commit()
    return book.authors


@router.delete("/{book_id}/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def remove_book_author(db: db_dependency, book_id: int, author_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri nuk gjendet!"
        )

    author = db.query(Author).filter(Author.id == author_id).first()
    if not author or author not in book.authors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky autor nuk eshte i lidhur me kete liber"
        )

    book.authors.remove(author)
    db.commit()


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def create_book(db: db_dependency, book: BookCreate):
    dupe_isbn = db.query(Book).filter(Book.isbn == book.isbn).first()

    if dupe_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Libri me kete isbn ekziston"
        )

    category = db.query(Category).filter(
        Category.id == book.category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kjo kategori nuk ekziston"
        )

    db_book = Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@router.put("/{book_id}", response_model=BookResponse, dependencies=[Depends(verify_api_key)])
async def update_book(db: db_dependency, book_id: int, book: BookCreate):
    book_exist = db.query(Book).filter(Book.id == book_id).first()

    if not book_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri me kete id nuk ekzistion"
        )

    # Isbn duhet me qene unik, por pa e llogarit vete kete liber
    dupe_isbn = db.query(Book).filter(
        Book.isbn == book.isbn,
        Book.id != book_id
    ).first()

    if dupe_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Libri me kete isbn ekziston"
        )

    category = db.query(Category).filter(
        Category.id == book.category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kjo kategori nuk ekziston"
        )

    book_exist.title = book.title
    book_exist.isbn = book.isbn
    book_exist.category_id = book.category_id
    book_exist.total_copies = book.total_copies
    book_exist.published_year = book.published_year

    db.commit()
    db.refresh(book_exist)
    return book_exist


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_book(db: db_dependency, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky liber nuk gjendet ne librari!"
        )

    active_loan = db.query(Loan).filter(
        Loan.book_id == book_id,
        Loan.return_date == None
    ).first()

    if active_loan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ky liber ka loan aktive"
        )

    # Huazimet e kthyera fshihen bashke me librin, perndryshe mbesin me book_id null
    db.query(Loan).filter(Loan.book_id == book_id).delete()
    db.delete(book)
    db.commit()
