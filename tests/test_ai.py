from datetime import date

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app import ai as ai_helper
from app.auth import API_KEY
from app.database import SessionLocal
from app.main import app
from app.models import Book, Category, Loan, Member
from app.routers import ai as ai_router
from app.routers import books as books_router
from app.routers import members as members_router

client = TestClient(app)

# Vektore te rreme me 1536 numra, secili tregon ne nje drejtim krejt tjeter
# Keshtu dihet saktesisht cili liber eshte me i afert, pa e thirr OpenAI
VECTOR_A = [1.0] + [0.0] * 1535
VECTOR_B = [0.0, 1.0] + [0.0] * 1534
VECTOR_C = [0.0, 0.0, 1.0] + [0.0] * 1533


def delete_test_data(db):
    test_books = db.query(Book).filter(Book.isbn.like("test-ai-%")).all()
    test_members = db.query(Member).filter(Member.email == "test-ai@example.com").all()

    for book in test_books:
        db.query(Loan).filter(Loan.book_id == book.id).delete()
    for member in test_members:
        db.query(Loan).filter(Loan.member_id == member.id).delete()
        db.delete(member)
    for book in test_books:
        db.delete(book)
    # Librat duhet me u fshi ne databaze para kategorise se tyre
    db.commit()

    db.query(Category).filter(Category.name == "test-ai-kategori").delete()
    db.commit()


# Fixture = kod qe ekzekutohet para dhe pas secilit test qe e kerkon
# Krijon nje kategori, dy libra dhe nje anetar qe e ka huazuar librin A
# Ne fund i fshin, qe databaza te mbetet si ishte
@pytest.fixture
def test_data():
    db = SessionLocal()
    delete_test_data(db)

    category = Category(name="test-ai-kategori")
    db.add(category)
    db.commit()

    book_a = Book(title="Test Libri A", isbn="test-ai-a", category_id=category.id,
                  total_copies=1, published_year=date(2020, 1, 1), embedding=VECTOR_A)
    book_b = Book(title="Test Libri B", isbn="test-ai-b", category_id=category.id,
                  total_copies=1, published_year=date(2020, 1, 1), embedding=VECTOR_B)
    member = Member(full_name="Test Anetari", email="test-ai@example.com",
                    join_date=date(2026, 1, 1))
    db.add_all([book_a, book_b, member])
    db.commit()

    loan = Loan(member_id=member.id, book_id=book_a.id,
                loan_date=date(2026, 1, 1), due_date=date(2026, 1, 15))
    db.add(loan)
    db.commit()

    yield {"book_a": book_a.id, "book_b": book_b.id, "member": member.id}

    delete_test_data(db)
    db.close()


# Pyetja merr vektorin e librit A, prandaj libri A duhet me dal i pari
def test_semantic_search_returns_closest_book_first(test_data, monkeypatch):
    # monkeypatch e zevendeson funksionin vetem gjate ketij testi
    monkeypatch.setattr(books_router, "create_embedding", lambda text: VECTOR_A)

    response = client.get("/api/v1/books/semantic-search?q=cfaredo&limit=3")

    assert response.status_code == 200
    results = response.json()
    assert results[0]["id"] == test_data["book_a"]
    assert results[0]["similarity"] > 0.99
    assert "embedding" not in results[0]


# Modeli i rreme kthen nje id te vertete dhe nje te shpikur (999999)
# API duhet ta ktheje vetem id-ne qe ishte te librat e gjetur
def test_librarian_rejects_book_id_that_was_not_retrieved(test_data, monkeypatch):
    def fake_ask_model(system, user):
        if system == ai_router.SEARCH_PROMPT:
            return '{"query": "test", "language": "en"}'
        return '{"answer": "Lexo keto.", "book_ids": [%d, 999999]}' % test_data["book_a"]

    monkeypatch.setattr(ai_router, "create_embedding", lambda text: VECTOR_A)
    monkeypatch.setattr(ai_router, "ask_model", fake_ask_model)

    response = client.post("/api/v1/ai/ask",
                           headers={"X-API-Key": API_KEY},
                           json={"question": "dua nje liber"})

    assert response.status_code == 200
    assert response.json()["book_ids"] == [test_data["book_a"]]


# Vektori C nuk eshte afer asnje libri, pra pergjigjja duhet me qene "nuk gjeta"
# Modeli thirret vetem nje here (per kerkimin), jo per pergjigjen
def test_librarian_says_so_when_nothing_is_relevant(test_data, monkeypatch):
    calls = []

    def fake_ask_model(system, user):
        calls.append(system)
        return '{"query": "test", "language": "sq"}'

    monkeypatch.setattr(ai_router, "create_embedding", lambda text: VECTOR_C)
    monkeypatch.setattr(ai_router, "ask_model", fake_ask_model)

    response = client.post("/api/v1/ai/ask",
                           headers={"X-API-Key": API_KEY},
                           json={"question": "receta gatimi"})

    assert response.status_code == 200
    assert response.json()["book_ids"] == []
    assert response.json()["answer"] == ai_router.NO_BOOKS_ANSWER["sq"]
    assert len(calls) == 1


# Anetari i testit e ka huazuar librin A, pra A nuk guxon me dal te rekomandimet
def test_recommendations_never_include_borrowed_books(test_data, monkeypatch):
    monkeypatch.setattr(members_router, "ask_model",
                        lambda system, user: '{"recommendations": []}')

    response = client.get(
        f"/api/v1/members/{test_data['member']}/recommendations?limit=10")

    assert response.status_code == 200
    recommended_ids = [book["id"] for book in response.json()]
    assert len(recommended_ids) > 0
    assert test_data["book_a"] not in recommended_ids


# Klienti i rreme i OpenAI deshton gjithmone, API duhet me kthy 503 e jo 500
def test_openai_error_returns_503(monkeypatch):
    class BrokenOpenAI:
        def __init__(self, **kwargs):
            raise OpenAIError("OpenAI nuk pergjigjet")

    monkeypatch.setattr(ai_helper, "OpenAI", BrokenOpenAI)

    response = client.get("/api/v1/books/semantic-search?q=cfaredo")

    assert response.status_code == 503
    assert response.json()["detail"] == "Sherbimi AI nuk eshte i disponueshem per momentin"
