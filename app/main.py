from sqlalchemy.orm import Session
from typing_extensions import Annotated

from fastapi import Depends, FastAPI, status
from database import engine, SessionLocal, get_db

app = FastAPI()

db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "library": "open"}
