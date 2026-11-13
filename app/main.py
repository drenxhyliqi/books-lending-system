import os

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from app.routers import members, books, authors, categories, loans, reports, ai


app = FastAPI()
app.include_router(members.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(authors.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")


@app.get("/api/v1/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "library": "open"}


# Frontend-i sherbehet nga i njejti server, keshtu nuk na duhet CORS
# Duhet me qene ne fund, perndryshe i mbulon endpoint-at e API-se
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
