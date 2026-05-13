from datetime import date
from typing import Optional

from pydantic import BaseModel


# Member Class Validation
class MemberBase(BaseModel):
    full_name: str
    email: str
    join_date: date
    is_active: bool = True


class MemberCreate(MemberBase):
    pass


class MemberResponse(MemberBase):
    id: int

    class Config:
        from_attributes = True
        # perdoret config per arsye se databaza kthen objekt,
        # ndersa fastapi pret
        # pydantic{pra validon te dhenat para se ti dergoj nga useri ne databaze dhe i kthen nga objekti ne JSON te dhenat qe vijn nga databaza}


# Author Class Validation
class AuthorBase(BaseModel):
    full_name: str
    country: str


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    id: int

    class Config:
        from_attributes = True


# Category Class Validation
class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int  # Per shkak se eshte autoincrement dhe kthehet nga databaza

    class Config:
        from_attributes = True

# Book Class Validation


class BookBase(BaseModel):
    title: str
    isbn: str
    category_id: int
    total_copies: int
    published_year: date


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True


# Book Author nuk ka nevoj per schema
# Pasi qe eshte vetem ure lidhese mes Books dhe Authors
# Pra nuk e perdorim asnjehere si nje API endpoint

# Loan Class Validation
class LoanBase(BaseModel):
    member_id: int
    book_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None


class LoanCreate(LoanBase):
    pass


class LoanResponse(LoanBase):
    id: int

    class Config:
        from_attributes = True
