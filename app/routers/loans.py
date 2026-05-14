from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Loan, Member
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

    return db.query(Loan).offset(offset).limit(page_size).all()
