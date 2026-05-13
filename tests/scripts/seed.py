
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa: E402

from app.models import Member, Author, Category, Book, BookAuthor, Loan
from app.database import SessionLocal
from datetime import date


def seed():
    db = SessionLocal()

    try:
        # ── CATEGORIES (4) ──────────────────────────
        categories = [
            Category(name="Fiction"),
            Category(name="Science"),
            Category(name="Technology"),
            Category(name="History"),
        ]
        db.add_all(categories)
        db.commit()
        for c in categories:
            db.refresh(c)

        # ── AUTHORS (8) ─────────────────────────────
        authors = [
            Author(full_name="Robert Martin", country="USA"),
            Author(full_name="George Orwell", country="UK"),
            Author(full_name="Erich Gamma", country="Germany"),
            Author(full_name="Richard Helm", country="USA"),
            Author(full_name="Stephen Hawking", country="UK"),
            Author(full_name="Yuval Harari", country="Israel"),
            Author(full_name="Frank Herbert", country="USA"),
            Author(full_name="Andrew Hunt", country="USA"),
        ]
        db.add_all(authors)
        db.commit()
        for a in authors:
            db.refresh(a)

        # ── BOOKS (20) ──────────────────────────────
        books = [
            # Technology
            Book(title="Clean Code", isbn="978-0132350884",
                 category_id=categories[2].id, total_copies=5, published_year=date(2008, 1, 1)),
            Book(title="The Pragmatic Programmer", isbn="978-0201616224",
                 category_id=categories[2].id, total_copies=4, published_year=date(1999, 1, 1)),
            Book(title="Design Patterns", isbn="978-0201633610",
                 category_id=categories[2].id, total_copies=3, published_year=date(1994, 1, 1)),
            Book(title="Refactoring", isbn="978-0134757599",
                 category_id=categories[2].id, total_copies=4, published_year=date(2018, 1, 1)),
            Book(title="The Clean Coder", isbn="978-0137081073",
                 category_id=categories[2].id, total_copies=3, published_year=date(2011, 1, 1)),
            # Fiction
            Book(title="1984", isbn="978-0451524935",
                 category_id=categories[0].id, total_copies=6, published_year=date(1949, 1, 1)),
            Book(title="Animal Farm", isbn="978-0451526342",
                 category_id=categories[0].id, total_copies=5, published_year=date(1945, 1, 1)),
            Book(title="Dune", isbn="978-0441013593",
                 category_id=categories[0].id, total_copies=4, published_year=date(1965, 1, 1)),
            Book(title="Dune Messiah", isbn="978-0441015221",
                 category_id=categories[0].id, total_copies=3, published_year=date(1969, 1, 1)),
            Book(title="Brave New World", isbn="978-0060850524",
                 category_id=categories[0].id, total_copies=4, published_year=date(1932, 1, 1)),
            # Science
            Book(title="A Brief History of Time", isbn="978-0553380163",
                 category_id=categories[1].id, total_copies=5, published_year=date(1988, 1, 1)),
            Book(title="The Grand Design", isbn="978-0553384666",
                 category_id=categories[1].id, total_copies=3, published_year=date(2010, 1, 1)),
            Book(title="Sapiens", isbn="978-0062316097",
                 category_id=categories[1].id, total_copies=6, published_year=date(2011, 1, 1)),
            Book(title="Homo Deus", isbn="978-0062464316",
                 category_id=categories[1].id, total_copies=4, published_year=date(2015, 1, 1)),
            Book(title="21 Lessons", isbn="978-0525512172",
                 category_id=categories[1].id, total_copies=3, published_year=date(2018, 1, 1)),
            # History
            Book(title="Guns Germs and Steel", isbn="978-0393317558",
                 category_id=categories[3].id, total_copies=4, published_year=date(1997, 1, 1)),
            Book(title="The Silk Roads", isbn="978-1408839997",
                 category_id=categories[3].id, total_copies=3, published_year=date(2015, 1, 1)),
            Book(title="SPQR", isbn="978-1631492228",
                 category_id=categories[3].id, total_copies=3, published_year=date(2015, 1, 1)),
            Book(title="The History of Rome", isbn="978-0679722328",
                 category_id=categories[3].id, total_copies=2, published_year=date(1976, 1, 1)),
            Book(title="Civilization", isbn="978-0143122050",
                 category_id=categories[3].id, total_copies=3, published_year=date(2011, 1, 1)),
        ]
        db.add_all(books)
        db.commit()
        for b in books:
            db.refresh(b)

        # ── BOOK AUTHORS ────────────────────────────
        book_authors = [
            # Një autor
            # Clean Code - Robert Martin
            BookAuthor(book_id=books[0].id, author_id=authors[0].id),
            # The Clean Coder - Robert Martin
            BookAuthor(book_id=books[4].id, author_id=authors[0].id),
            # 1984 - George Orwell
            BookAuthor(book_id=books[5].id, author_id=authors[1].id),
            # Animal Farm - George Orwell
            BookAuthor(book_id=books[6].id, author_id=authors[1].id),
            # Dune - Frank Herbert
            BookAuthor(book_id=books[7].id, author_id=authors[6].id),
            # Dune Messiah - Frank Herbert
            BookAuthor(book_id=books[8].id, author_id=authors[6].id),
            # Brief History - Hawking
            BookAuthor(book_id=books[10].id, author_id=authors[4].id),
            # Sapiens - Harari
            BookAuthor(book_id=books[12].id, author_id=authors[5].id),
            # Homo Deus - Harari
            BookAuthor(book_id=books[13].id, author_id=authors[5].id),
            # 21 Lessons - Harari
            BookAuthor(book_id=books[14].id, author_id=authors[5].id),
            # Shumë autorë (3 libra me më shumë se 1 autor)
            # Design Patterns - Gamma
            BookAuthor(book_id=books[2].id, author_id=authors[2].id),
            # Design Patterns - Helm
            BookAuthor(book_id=books[2].id, author_id=authors[3].id),
            # Pragmatic - Hunt
            BookAuthor(book_id=books[1].id, author_id=authors[7].id),
            # Pragmatic - Martin
            BookAuthor(book_id=books[1].id, author_id=authors[0].id),
            # Grand Design - Hawking
            BookAuthor(book_id=books[11].id, author_id=authors[4].id),
            # Grand Design - Harari
            BookAuthor(book_id=books[11].id, author_id=authors[5].id),
        ]
        db.add_all(book_authors)
        db.commit()

        # ── MEMBERS (10) ────────────────────────────
        members = [
            Member(full_name="Ana Krasniqi", email="ana@gmail.com",
                   join_date=date(2023, 1, 15), is_active=True),
            Member(full_name="Besim Hoxha", email="besim@gmail.com",
                   join_date=date(2023, 2, 20), is_active=True),
            Member(full_name="Drita Osmani", email="drita@gmail.com",
                   join_date=date(2023, 3, 10), is_active=True),
            Member(full_name="Faton Berisha", email="faton@gmail.com",
                   join_date=date(2023, 4, 5), is_active=True),
            Member(full_name="Genta Lleshi", email="genta@gmail.com",
                   join_date=date(2023, 5, 12), is_active=True),
            Member(full_name="Ilir Morina", email="ilir@gmail.com",
                   join_date=date(2023, 6, 8), is_active=True),
            Member(full_name="Kaltrina Gashi", email="kaltrina@gmail.com",
                   join_date=date(2023, 7, 22), is_active=True),
            Member(full_name="Luan Bajrami", email="luan@gmail.com",
                   join_date=date(2023, 8, 18), is_active=True),
            Member(full_name="Mimoza Avdiu", email="mimoza@gmail.com",
                   join_date=date(2023, 9, 3), is_active=False),
            Member(full_name="Nita Sylaj", email="nita@gmail.com",
                   join_date=date(2023, 10, 14), is_active=True),
        ]
        db.add_all(members)
        db.commit()
        for m in members:
            db.refresh(m)

        # ── LOANS (30) ──────────────────────────────
        loans = [
            # Returned loans (return_date ka vlerë)
            Loan(member_id=members[0].id, book_id=books[0].id, loan_date=date(
                2024, 1, 1), due_date=date(2024, 1, 15), return_date=date(2024, 1, 10)),
            Loan(member_id=members[1].id, book_id=books[1].id, loan_date=date(
                2024, 1, 5), due_date=date(2024, 1, 20), return_date=date(2024, 1, 18)),
            Loan(member_id=members[2].id, book_id=books[2].id, loan_date=date(
                2024, 2, 1), due_date=date(2024, 2, 15), return_date=date(2024, 2, 12)),
            Loan(member_id=members[3].id, book_id=books[3].id, loan_date=date(
                2024, 2, 10), due_date=date(2024, 2, 25), return_date=date(2024, 2, 20)),
            Loan(member_id=members[4].id, book_id=books[4].id, loan_date=date(
                2024, 3, 1), due_date=date(2024, 3, 15), return_date=date(2024, 3, 14)),
            Loan(member_id=members[5].id, book_id=books[5].id, loan_date=date(
                2024, 3, 5), due_date=date(2024, 3, 20), return_date=date(2024, 3, 19)),
            Loan(member_id=members[6].id, book_id=books[6].id, loan_date=date(
                2024, 4, 1), due_date=date(2024, 4, 15), return_date=date(2024, 4, 10)),
            Loan(member_id=members[7].id, book_id=books[7].id, loan_date=date(
                2024, 4, 5), due_date=date(2024, 4, 20), return_date=date(2024, 4, 18)),
            Loan(member_id=members[8].id, book_id=books[8].id, loan_date=date(
                2024, 5, 1), due_date=date(2024, 5, 15), return_date=date(2024, 5, 12)),
            Loan(member_id=members[9].id, book_id=books[9].id, loan_date=date(
                2024, 5, 5), due_date=date(2024, 5, 20), return_date=date(2024, 5, 19)),
            Loan(member_id=members[0].id, book_id=books[10].id, loan_date=date(
                2024, 6, 1), due_date=date(2024, 6, 15), return_date=date(2024, 6, 14)),
            Loan(member_id=members[1].id, book_id=books[11].id, loan_date=date(
                2024, 6, 5), due_date=date(2024, 6, 20), return_date=date(2024, 6, 18)),

            # Active loans (return_date = NULL, due_date në të ardhmen)
            Loan(member_id=members[0].id, book_id=books[12].id, loan_date=date(
                2026, 4, 20), due_date=date(2026, 5, 20), return_date=None),
            Loan(member_id=members[1].id, book_id=books[13].id, loan_date=date(
                2026, 4, 22), due_date=date(2026, 5, 22), return_date=None),
            Loan(member_id=members[2].id, book_id=books[14].id, loan_date=date(
                2026, 4, 25), due_date=date(2026, 5, 25), return_date=None),
            Loan(member_id=members[3].id, book_id=books[15].id, loan_date=date(
                2026, 5, 1), due_date=date(2026, 5, 30), return_date=None),
            Loan(member_id=members[4].id, book_id=books[16].id, loan_date=date(
                2026, 5, 3), due_date=date(2026, 6, 3), return_date=None),
            Loan(member_id=members[5].id, book_id=books[17].id, loan_date=date(
                2026, 5, 5), due_date=date(2026, 6, 5), return_date=None),

            # Overdue loans (due_date në të kaluarën, return_date = NULL)
            Loan(member_id=members[6].id, book_id=books[18].id, loan_date=date(
                2026, 3, 1), due_date=date(2026, 3, 15), return_date=None),
            Loan(member_id=members[7].id, book_id=books[19].id, loan_date=date(
                2026, 3, 5), due_date=date(2026, 3, 20), return_date=None),
            Loan(member_id=members[8].id, book_id=books[0].id, loan_date=date(
                2026, 3, 10), due_date=date(2026, 3, 25), return_date=None),
            Loan(member_id=members[9].id, book_id=books[1].id, loan_date=date(
                2026, 3, 12), due_date=date(2026, 3, 27), return_date=None),
            Loan(member_id=members[0].id, book_id=books[2].id, loan_date=date(
                2026, 2, 1), due_date=date(2026, 2, 15), return_date=None),
            Loan(member_id=members[1].id, book_id=books[3].id, loan_date=date(
                2026, 2, 5), due_date=date(2026, 2, 20), return_date=None),
            Loan(member_id=members[2].id, book_id=books[4].id, loan_date=date(
                2026, 2, 10), due_date=date(2026, 2, 25), return_date=None),
            Loan(member_id=members[3].id, book_id=books[5].id, loan_date=date(
                2026, 1, 1), due_date=date(2026, 1, 15), return_date=None),
            Loan(member_id=members[4].id, book_id=books[6].id, loan_date=date(
                2026, 1, 5), due_date=date(2026, 1, 20), return_date=None),
            Loan(member_id=members[5].id, book_id=books[7].id, loan_date=date(
                2026, 1, 10), due_date=date(2026, 1, 25), return_date=None),
            Loan(member_id=members[6].id, book_id=books[8].id, loan_date=date(
                2025, 12, 1), due_date=date(2025, 12, 15), return_date=None),
            Loan(member_id=members[7].id, book_id=books[9].id, loan_date=date(
                2025, 12, 5), due_date=date(2025, 12, 20), return_date=None),
            Loan(member_id=members[8].id, book_id=books[10].id, loan_date=date(
                2025, 12, 10), due_date=date(2025, 12, 25), return_date=None),
        ]
        db.add_all(loans)
        db.commit()

        print("Seed data u shtua me sukses")
        print(f"   {len(categories)} categories")
        print(f"   {len(authors)} authors")
        print(f"   {len(books)} books")
        print(f"   {len(members)} members")
        print(f"   {len(loans)} loans")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
