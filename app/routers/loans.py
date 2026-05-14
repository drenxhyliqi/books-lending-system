from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Loan, Member, Book
from app.schemas import LoanCreate, LoanResponse

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/loans", tags=["loans"])
db_dependency = Annotated[Session, Depends(get_db)]


# GET / loans(filter: active, overdue, member_id) # check
# POST / loans
# PUT    / loans/{id}/return


@router.get("/", response_model=list[LoanResponse], status_code=status.HTTP_200_OK)
async def get_loans(db: db_dependency,
                    active: bool | None = None,
                    overdue: bool | None = None,
                    member_id: int | None = None,
                    page: int = 1,
                    page_size: int = 50
                    ):
    query = db.query(Loan)
    offset = (page - 1) * page_size

    # Filtrimi 1
    if active is not None:
        if active:
            query = query.filter(Loan.return_date == None)
        else:
            query = query.filter(Loan.return_date != None)

    # Filtrimi 2
    if overdue is not None:
        if overdue:
            query = query.filter(
                Loan.due_date < date.today(),
                Loan.return_date == None
            )
        else:
            query = query.filter(Loan.due_date >= date.today())

    # Filtrimi 3
    if member_id is not None:
        query = query.filter(Loan.member_id == member_id)

    return query(Loan).offset(offset).limit(page_size).all()


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(db: db_dependency, create_loan: LoanCreate):
    # Validimi 1 - A eshte anetar aktiv?
    member = db.query(Member).filter(
        Member.id == create_loan.member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky anetar nuk ekziston"
        )
    if not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ky anetar nuk eshte aktiv"
        )

    # Validimi 2 - a ka kopje
    active_loans = db.query(Loan).filter(
        Loan.book_id == create_loan.book_id,
        Loan.return_date == None
    ).count()

    book = db.query(Book).filter(Book.id == create_loan.book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libri nuk u gjet"
        )

    if book.total_copies <= active_loans:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nuk ka kopje te disponueshme"
        )

    # Validimi 3 - Loan date nga dita kur merr loan
    db_loan = Loan(
        member_id=create_loan.member_id,
        book_id=create_loan.book_id,
        due_date=create_loan.due_date,
        loan_date=date.today()
    )
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


@router.post("/{book_id}/return")
async def return_book(db: db_dependency, loan_id: int):
    # Validimi 1 a ekziston ky loan
    loan = db.query(Loan).filter(Loan.id == loan_id).first()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky loan nuk ekziston"
        )

    # Validimi 2 libri eshte kthyer me heret

    if loan.return_date is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Libri eshte kthyer tashme!"
        )

    loan.return_date = date.today()
    db.commit()
    db.refresh(loan)
    return loan
