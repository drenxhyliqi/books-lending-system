# Books Lending System

A backend API for managing a small library — members borrow books, books have authors, and the system keeps track of who has what and for how long. Built with FastAPI, PostgreSQL, and SQLAlchemy.

---

## Getting Started

### Prerequisites

- Python 3.13
- PostgreSQL with the pgvector extension
- (Optional) Docker

### Installation

```bash
# Clone the repository
git clone https://github.com/drenxhyliqi/books-lending-system.git
cd books-lending-system

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/books_lending
API_KEY=library-secret-key
OPENAI_API_KEY=your-openai-key
OPENAI_CHAT_MODEL=gpt-6.1-sol
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Database Setup

### Run migrations

```bash
alembic upgrade head
```

### Seed the database with test data

```bash
python tests/scripts/seed.py
```

This will populate the database with:
- 4 categories
- 8 authors
- 20 books
- 10 members
- 31 loans (mix of active, returned, and overdue)

### Create embeddings for the books

```bash
python tests/scripts/embed_books.py
```

This calls the OpenAI API once for every book that has no embedding yet (needs `OPENAI_API_KEY`). Semantic search only finds books that have an embedding. Books created or updated through the API get their embedding automatically.

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

### Frontend

The same server also serves a small web interface at `http://localhost:8000/`. It is plain HTML, CSS and JavaScript in the `frontend/` folder, with no build step. To add, edit or delete anything, type the API key in the field at the top of the page.

---

## Running with Docker

```bash
docker compose up
```

This starts both the FastAPI app and a PostgreSQL database, and applies migrations on startup. The API will be available at `http://localhost:8000`.

If ports 8000 or 5432 are already in use, set `API_PORT` and/or `DB_PORT` (in `.env` or your shell) to pick different host ports.

To seed the Docker database:

```bash
docker compose exec api python tests/scripts/seed.py
```

Make sure you have a `.env.docker` file:

```
DATABASE_URL=postgresql://postgres:yourpassword@db:5432/books_lending
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=books_lending
API_KEY=library-secret-key
OPENAI_API_KEY=your-openai-key
OPENAI_CHAT_MODEL=gpt-6.1-sol
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Running Tests

```bash
pytest tests/ -v
```

The tests need the database running with migrations applied. They never call OpenAI (the calls are replaced with fakes), and each test creates its own rows and deletes them afterwards.

---

## Authentication

Some endpoints require an API key. Pass it as a request header:

```
X-API-Key: library-secret-key
```

Protected endpoints (require API key):
- All `POST` endpoints
- All `PUT` / `PATCH` endpoints
- All `DELETE` endpoints

`GET` endpoints are open — no key needed.

---

## Endpoints

### Health
```
GET  /api/v1/health
```

### Members
```
GET    /api/v1/members/
GET    /api/v1/members/{id}
GET    /api/v1/members/{id}/loans
GET    /api/v1/members/{id}/recommendations
POST   /api/v1/members/
PUT    /api/v1/members/{id}
DELETE /api/v1/members/{id}
```

### Books
```
GET    /api/v1/books/
GET    /api/v1/books/search
GET    /api/v1/books/semantic-search
GET    /api/v1/books/{id}
GET    /api/v1/books/{id}/authors
GET    /api/v1/books/{id}/loan-history
POST   /api/v1/books/
PUT    /api/v1/books/{id}
DELETE /api/v1/books/{id}
POST   /api/v1/books/{id}/authors/{author_id}
DELETE /api/v1/books/{id}/authors/{author_id}
```

### Authors
```
GET    /api/v1/authors/
GET    /api/v1/authors/{id}
POST   /api/v1/authors/
```

### Categories
```
GET    /api/v1/categories/
POST   /api/v1/categories/
```

### Loans
```
GET    /api/v1/loans/
POST   /api/v1/loans/
POST   /api/v1/loans/{id}/return
```

### Reports
```
GET    /api/v1/reports/top-borrowers
GET    /api/v1/reports/overdue-loans
```

### AI
```
POST   /api/v1/ai/ask
```

---

## AI features

These use the OpenAI API and the pgvector extension. Every book has an embedding, a list of 1536 numbers that represents the meaning of its title, description, category and authors. The model only ever sees books that were found in the database.

### Semantic search

Finds books by meaning instead of matching words in the title. Works best with English queries, because the book descriptions are in English.

```
GET /api/v1/books/semantic-search?q=space and black holes&limit=2
```

```json
[
  {
    "title": "A Brief History of Time",
    "isbn": "978-0553380163",
    "category_id": 2,
    "total_copies": 5,
    "published_year": "1988-01-01",
    "description": "An accessible tour of cosmology: the big bang, black holes, the nature of time and the search for a unified theory.",
    "id": 11,
    "similarity": 0.35
  },
  {
    "title": "The Grand Design",
    "isbn": "978-0553384666",
    "category_id": 2,
    "total_copies": 3,
    "published_year": "2010-01-01",
    "description": "A popular science book arguing that the laws of physics can explain why the universe exists, including M-theory and multiple universes.",
    "id": 12,
    "similarity": 0.3119
  }
]
```

`similarity` is `1 - cosine distance`, so a higher number means a closer match.

### AI librarian

Answers a question in Albanian or English and recommends books from the library. Requires the API key.

```
POST /api/v1/ai/ask
X-API-Key: library-secret-key

{ "question": "me duhet te lexoj dicka per universin" }
```

```json
{
  "answer": "Për të lexuar për universin, të rekomandoj të fillosh me “A Brief History of Time”, që shpjegon Big Bengun, vrimat e zeza dhe natyrën e kohës në mënyrë të kuptueshme. Më pas mund të lexosh “The Grand Design”, që trajton ligjet e fizikës, ekzistencën e universit dhe idenë e universeve të shumëfishta.",
  "book_ids": [11, 12]
}
```

How it works:

1. The model turns the question into a short English search query.
2. The query is embedded and the 5 closest books are loaded from the database.
3. If even the closest book is below a similarity of 0.35, the API answers that the library has no book for this, without asking the model again.
4. Otherwise the model gets only those 5 books and writes the answer.
5. Any `book_id` in the answer that was not one of those 5 books is removed.

When the library has nothing that fits:

```json
{
  "answer": "Nuk gjeta asnje liber ne biblioteke qe i pershtatet kesaj. Me trego nje teme ose lloj libri qe te intereson.",
  "book_ids": []
}
```

In the web interface this is the "Bibliotekari" page.

### Recommendations for a member

Suggests books that are similar to what the member has borrowed and that they have never borrowed. Only book titles and descriptions are sent to the model, never the member's name or email.

```
GET /api/v1/members/1/recommendations?limit=3
```

```json
[
  {
    "title": "The Clean Coder",
    "isbn": "978-0137081073",
    "category_id": 3,
    "total_copies": 3,
    "published_year": "2011-01-01",
    "description": "A code of conduct for professional programmers: estimates, pressure, saying no, and taking responsibility for your work.",
    "id": 5,
    "reason": "Plotëson parimet e Clean Code me këshilla për përgjegjësinë dhe sjelljen profesionale të programuesit."
  }
]
```

If the member has no loans yet, the most borrowed books are returned and the model is not called.

### Errors

If OpenAI cannot be reached, the key is wrong, or the model returns something that does not match the expected shape, these endpoints return `503` with a message in Albanian.

---

## Notes

lighthouse

This project helped me a lot overall. Some things were mentioned in the course but not covered in detail, working through them here helped me understand them much better

The toughest part was `loans.py`, especially the filtering logic and the validations around borrowing. Getting the active loan checks and the status filters right took more time than I expected. Everything else felt more straightforward once I had the database and models set up properly.

The biggest thing I learned was how a backend system actually comes together, the database connection, the models, the schemas, and how data goes all the way to whoever is consuming the API. Alembic was new to me and I really liked it, basically I learnt that is like Git but for your database, letting you update the schema without wiping everything and starting over

If I had more time, I would replace the API key auth with a proper admin user system. Regular users would only have access to GET endpoints, while admins would get a JWT token on login and that token would be required for any endpoint that creates, updates, or deletes data.

I know this is not a good approach but if you need the key to test the api endpoints that require that, here is it 'library-secret-key' I added this on the .env file but since you can not have access in that, and you might need it to test the endpoints I will add it here.