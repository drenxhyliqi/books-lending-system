# Books Lending System

A backend API for managing a small library — members borrow books, books have authors, and the system keeps track of who has what and for how long. Built with FastAPI, PostgreSQL, and SQLAlchemy.

---

## Getting Started

### Prerequisites

- Python 3.13
- PostgreSQL
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

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

---

## Running with Docker

```bash
docker compose up
```

This starts both the FastAPI app and a PostgreSQL database. The API will be available at `http://localhost:8000`.

Make sure you have a `.env.docker` file:

```
DATABASE_URL=postgresql://postgres:yourpassword@db:5432/books_lending
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=books_lending
API_KEY=library-secret-key
```

---

## Running Tests

```bash
pytest tests/ -v
```

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
POST   /api/v1/members/
PUT    /api/v1/members/{id}
DELETE /api/v1/members/{id}
```

### Books
```
GET    /api/v1/books/
GET    /api/v1/books/search
GET    /api/v1/books/{id}
GET    /api/v1/books/{id}/authors
GET    /api/v1/books/{id}/loan-history
POST   /api/v1/books/
PUT    /api/v1/books/{id}
DELETE /api/v1/books/{id}
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

---

## Notes

lighthouse

This project helped me a lot overall. Some things were mentioned in the course but not covered in detail, working through them here helped me understand them much better

The toughest part was `loans.py`, especially the filtering logic and the validations around borrowing. Getting the active loan checks and the status filters right took more time than I expected. Everything else felt more straightforward once I had the database and models set up properly.

The biggest thing I learned was how a backend system actually comes together, the database connection, the models, the schemas, and how data goes all the way to whoever is consuming the API. Alembic was new to me and I really liked it, basically I learnt that is like Git but for your database, letting you update the schema without wiping everything and starting over

If I had more time, I would replace the API key auth with a proper admin user system. Regular users would only have access to GET endpoints, while admins would get a JWT token on login and that token would be required for any endpoint that creates, updates, or deletes data.

I know this is not a good approach but if you need the key to test the api endpoints that require that, here is it 'apikeylibrary' I added this on the .env file but since you can not have access in that, and you might need it to test the endpoints I will add it here.