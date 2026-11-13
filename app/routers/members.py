from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
# Auth
from app.auth import verify_api_key

# Database imports
from app.database import get_db
from app.models import Book, Member, Loan
from app.schemas import BookRecommendation, LoanResponse, MemberCreate, MemberResponse, RecommendationReasons
from app.ai import ask_model, book_to_text

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/members", tags=["members"])
db_dependency = Annotated[Session, Depends(get_db)]

# APIEndpoint - Merri te gjithe anetare + filter_active(true/false) #check
# APIEndpoint - Merre nje anetar specifk #check
# APIEndpoint - Krijo nje anetar #check
# APIEndpoint - Perditeso nje anetar specifk #check
# APIEndpoint - Fshij nje anetar specifk #check
# APIEndpoint - Rekomando libra per nje anetar sipas huazimeve te tij

RECOMMEND_PROMPT = (
    "You are the librarian of a small library. "
    "You get the books a member has borrowed and a list of recommended books. "
    "For each recommended book write one short sentence in Albanian that says "
    "why it fits someone who borrowed those books. "
    "Use only the ids of the recommended books. "
    'Reply only with JSON in the form '
    '{"recommendations": [{"book_id": 1, "reason": "..."}]}.'
)


@router.get("/", response_model=list[MemberResponse])  # Get member me filter
async def get_members(db: db_dependency,
                      is_active: bool | None = None,
                      page: int = Query(1, ge=1),
                      page_size: int = Query(100, ge=1)
                      ):
    query = db.query(Member)  # SELECT * FROM members
    offset = (page - 1) * page_size
    if is_active is not None:  # WHERE is_active = true
        query = query.filter(Member.is_active == is_active)
    # Ekzekuton queryn
    return query.order_by(Member.id).offset(offset).limit(page_size).all()


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(db: db_dependency, member_id: int):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pjestari nuk u gjet!'
        )
    return member


@router.get("/{member_id}/loans", response_model=list[LoanResponse])
async def get_member_loans(db: db_dependency, member_id: int):
    member = db.query(Member).filter(Member.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anetari nuk u gjet!"
        )

    return member.loans  # SELECT * FROM loans WHERE memb_id = 1


@router.get("/{member_id}/recommendations", response_model=list[BookRecommendation])
async def get_member_recommendations(db: db_dependency,
                                     member_id: int,
                                     limit: int = Query(3, ge=1, le=10)
                                     ):
    member = db.query(Member).filter(Member.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anetari nuk u gjet!"
        )

    borrowed_ids = [loan.book_id for loan in member.loans]
    borrowed = db.query(Book).filter(
        Book.id.in_(borrowed_ids),
        Book.embedding != None
    ).all()

    # Pa huazime nuk dihet shija e anetarit, kthehen librat me te huazuar
    # Njejt si top-borrowers te reports, dhe modeli nuk thirret fare
    if not borrowed:
        popular = (
            db.query(Book, func.count(Loan.id).label("total_loans"))
            .join(Loan)
            .group_by(Book.id)
            .order_by(func.count(Loan.id).desc())
            .limit(limit)
            .all()
        )

        return [
            BookRecommendation(
                id=book.id,
                title=book.title,
                isbn=book.isbn,
                category_id=book.category_id,
                total_copies=book.total_copies,
                published_year=book.published_year,
                description=book.description,
                reason="Nje nga librat me te huazuar ne biblioteke"
            )
            for book, total_loans in popular
        ]

    # Mesatarja e vektoreve te librave te huazuar = shija e anetarit si nje vektor
    # zip i merr numrat ne te njejtin pozicion nga secili vektor
    taste = [
        sum(values) / len(borrowed)
        for values in zip(*(book.embedding for book in borrowed))
    ]

    # Librat me te afert me ate shije, pa ata qe i ka huazuar ndonjehere
    candidates = (
        db.query(Book)
        .filter(Book.embedding != None, Book.id.notin_(borrowed_ids))
        .order_by(Book.embedding.cosine_distance(taste))
        .limit(limit)
        .all()
    )

    if not candidates:
        return []

    # Modelit i dergohen vetem librat, asnje e dhene e anetarit
    borrowed_text = "\n".join(f"- {book.title}: {book.description}" for book in borrowed)
    candidates_text = "\n\n".join(
        f"[id {book.id}]\n{book_to_text(book)}" for book in candidates
    )

    try:
        answer = RecommendationReasons.model_validate_json(ask_model(
            RECOMMEND_PROMPT,
            f"Borrowed books:\n{borrowed_text}\n\nRecommended books:\n{candidates_text}"
        ))
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modeli ktheu pergjigje te pavlefshme"
        )

    # Arsyet per id qe nuk jane te kandidatet hidhen poshte
    candidate_ids = [book.id for book in candidates]
    reasons = {
        item.book_id: item.reason
        for item in answer.recommendations if item.book_id in candidate_ids
    }

    return [
        BookRecommendation(
            id=book.id,
            title=book.title,
            isbn=book.isbn,
            category_id=book.category_id,
            total_copies=book.total_copies,
            published_year=book.published_year,
            description=book.description,
            reason=reasons.get(book.id, "I ngjashem me librat qe ke huazuar")
        )
        for book in candidates
    ]


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def create_member(db: db_dependency, member: MemberCreate):
    email_exist = db.query(Member).filter(Member.email == member.email).first()

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ky email tashme ekziston!"
        )
    # e bene destruct dictionaryn, per databaze e kthen nga "full_name":"name" ne full_name = "Name"
    db_member = Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.put("/{member_id}", response_model=MemberResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def update_member(db: db_dependency, member_id: int, member: MemberCreate):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky person nuk eshte nje anetar i biblotekes"
        )

    # Email duhet me qene unik, por pa e llogarit vete kete anetar
    email_exist = db.query(Member).filter(
        Member.email == member.email,
        Member.id != member_id
    ).first()

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ky email tashme ekziston!"
        )

    db_member.full_name = member.full_name
    db_member.email = member.email
    db_member.join_date = member.join_date
    db_member.is_active = member.is_active

    db.commit()
    db.refresh(db_member)
    return db_member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_member(db: db_dependency, member_id: int):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky anetar nuk ekziston!"
        )

    active_loan = db.query(Loan).filter(
        Loan.member_id == member_id,
        Loan.return_date == None
    ).first()

    if active_loan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ky anetar ka loan aktive"
        )

    # Huazimet e kthyera fshihen bashke me anetarin, perndryshe mbesin me member_id null
    db.query(Loan).filter(Loan.member_id == member_id).delete()
    db.delete(member)
    db.commit()
