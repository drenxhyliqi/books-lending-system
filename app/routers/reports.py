from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Annotated

from app.database import get_db
from app.models import Member, Loan
from app.schemas import TopBorrowerResponse, OverdueLoanResponse

router = APIRouter(prefix="/reports", tags=["reports"])
db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/top-borrowers", response_model=list[TopBorrowerResponse])
async def top_borrowers(db: db_dependency, limit: int = 5):

    results = (
        db.query(Member, func.count(Loan.id).label("total_loans")).join(Loan).group_by(
            Member.id).order_by(func.count(Loan.id).desc()).limit(limit).all()
    )

    return [
        TopBorrowerResponse(
            id=member.id,
            full_name=member.full_name,
            email=member.email,
            total_loans=total_loans
        )
        for member, total_loans in results
    ]


@router.get("/overdue-loans", response_model=list[OverdueLoanResponse])
async def overdue_loans(db: db_dependency):
    loans = (
        db.query(Loan)
        .filter(
            Loan.due_date < date.today(),
            Loan.return_date == None
        )
        .all()
    )

    return [
        OverdueLoanResponse(
            id=loan.id,
            member_name=loan.member.full_name,
            book_title=loan.book.title,
            due_date=loan.due_date,
            days_overdue=(date.today() - loan.due_date).days
        )
        for loan in loans
    ]
