from sqlalchemy.orm import Session
from typing_extensions import Annotated

from fastapi import Depends, FastAPI, status
from app.database import get_db
from app.routers import members, books, authors, categories, loans, reports


app = FastAPI()
app.include_router(members.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(authors.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/api/v1/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "library": "open"}
