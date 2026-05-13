
from app.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Date
# Mundeson navigim me te lehte mes tabelave
from sqlalchemy.orm import relationship


class Member(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    join_date = Column(Date)
    is_active = Column(Boolean, default=True)

    loans = relationship("Loan", back_populates="member")


class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    country = Column(String)

    books = relationship("Book", secondary="book_authors",
                         back_populates="authors")


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    books = relationship("Book", back_populates="category")


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    isbn = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    total_copies = Column(Integer, default=0)
    published_year = Column(Date)

    category = relationship("Category", back_populates="books")
    authors = relationship(
        "Author", secondary="book_authors", back_populates="books")
    loans = relationship("Loan", back_populates="book")


class BookAuthor(Base):
    __tablename__ = 'book_authors'
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True)
    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)


class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    loan_date = Column(Date)
    due_date = Column(Date)
    return_date = Column(Date, nullable=True)

    member = relationship("Member", back_populates="loans")
    book = relationship("Book", back_populates="loans")
