import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa: E402

from app.models import Book
from app.database import SessionLocal
from app.ai import book_to_text, create_embedding


def embed_books():
    db = SessionLocal()

    try:
        # Vetem librat pa embedding, qe te mos paguhet dy here per te njejtin liber
        books = db.query(Book).filter(Book.embedding == None).all()

        for book in books:
            book.embedding = create_embedding(book_to_text(book))
            db.commit()
            print(f"   {book.title}")

        print(f"Embedding u krijua per {len(books)} libra")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    embed_books()
