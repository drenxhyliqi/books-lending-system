from sqlalchemy.orm import Session
from typing_extensions import Annotated

from fastapi import Depends, FastAPI, status
from app.database import get_db
from app.routers import members, books, authors, categories, loans


app = FastAPI()
app.include_router(members.router)
app.include_router(books.router)
app.include_router(authors.router)
app.include_router(categories.router)
app.include_router(loans.router)


@app.get("/", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "library": "open"}
