from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Member
from app.schemas import MemberCreate, MemberResponse

# Per mos me shkru /members/... ne qdo endpoint prefix /
router = APIRouter(prefix="/members", tags=["members"])
db_dependency = Annotated[Session, Depends(get_db)]

# APIEndpoint - Merri te gjithe anetare + filter_active(true/false) #check
# APIEndpoint - Merre nje anetar specifk #check
# APIEndpoint - Krijo nje anetar #check
# APIEndpoint - Perditeso nje anetar specifk #check
# APIEndpoint - Fshij nje anetar specifk #check


@router.get("/", response_model=list[MemberResponse])  # Get member me filter
async def get_members(db: db_dependency, is_active: bool | None = None):
    query = db.query(Member)  # SELECT * FROM members
    if is_active is not None:  # WHERE is_active = true
        query = query.filter(Member.is_active == is_active)
    return query.all()  # Ekzekuton queryn


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(db: db_dependency, member_id: int):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pjestari nuk u gjet!'
        )
    return member


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{member_id}", response_model=MemberResponse, status_code=status.HTTP_200_OK)
async def update_member(db: db_dependency, member_id: int, member: MemberCreate):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky person nuk eshte nje anetar i biblotekes"
        )

    db_member.full_name = member.full_name
    db_member.email = member.email
    db_member.join_date = member.join_date
    db_member.is_active = member.is_active

    db.commit()
    db.refresh(db_member)
    return db_member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(db: db_dependency, member_id: int):
    is_member = db.query(Member).filter(Member.id == member_id).first()
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ky anetar nuk ekziston!"
        )
    db.delete(is_member)
    db.commit()
