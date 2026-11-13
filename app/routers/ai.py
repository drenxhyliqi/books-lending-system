from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status

# Database imports
from app.database import get_db
from app.models import Book
from app.schemas import AskRequest, AskResponse, SearchQuery
from app.auth import verify_api_key
from app.ai import ask_model, book_to_text, create_embedding

# Per mos me shkru /ai/... ne qdo endpoint prefix /
router = APIRouter(prefix="/ai", tags=["ai"])
db_dependency = Annotated[Session, Depends(get_db)]

# POST / ai/ask

# Nese edhe libri me i afert eshte nen kete vlere, biblioteka nuk ka liber per ate teme
MIN_SIMILARITY = 0.35

# Pershkrimet e librave jane ne anglisht, prandaj kerkimi behet ne anglisht
SEARCH_PROMPT = (
    "You turn a library visitor's message into a short English search query "
    "describing the kind of book they want. "
    "Also detect the language of the message: 'sq' for Albanian, 'en' for anything else. "
    'Reply only with JSON in the form {"query": "...", "language": "sq"}.'
)

ANSWER_PROMPT = (
    "You are the librarian of a small library. "
    "Recommend books ONLY from the list of books in the user message. "
    "Never mention a book that is not in that list. "
    "If none of the listed books fits the question, say so and return an empty book_ids list. "
    "Answer in the same language as the question (Albanian or English), "
    "in 2 to 4 sentences of plain text. "
    'Reply only with JSON in the form {"answer": "...", "book_ids": [1, 2]}, '
    "where book_ids are the ids of the books you recommend."
)

NO_BOOKS_ANSWER = {
    "sq": "Nuk gjeta asnje liber ne biblioteke qe i pershtatet kesaj. "
          "Me trego nje teme ose lloj libri qe te intereson.",
    "en": "I could not find a book in the library that fits this. "
          "Tell me a topic or kind of book you are interested in."
}


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
async def ask_librarian(db: db_dependency, ask: AskRequest):
    # Hapi 1 - modeli e kthen pyetjen ne nje kerkim te shkurter ne anglisht
    try:
        search = SearchQuery.model_validate_json(
            ask_model(SEARCH_PROMPT, ask.question))
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modeli ktheu pergjigje te pavlefshme"
        )

    # Hapi 2 - 5 librat me te afert me kerkimin (njejt si semantic-search)
    distance = Book.embedding.cosine_distance(create_embedding(search.query))
    results = (
        db.query(Book, distance.label("distance"))
        .filter(Book.embedding != None)
        .order_by(distance)
        .limit(5)
        .all()
    )

    # Hapi 3 - nese asnje liber nuk eshte mjaft i afert, modeli nuk pyetet fare
    if not results or 1 - results[0][1] < MIN_SIMILARITY:
        language = "sq" if search.language == "sq" else "en"
        return AskResponse(answer=NO_BOOKS_ANSWER[language], book_ids=[])

    # Hapi 4 - modeli i sheh vetem keta libra, jo krejt databazen
    books_text = "\n\n".join(
        f"[id {book.id}]\n{book_to_text(book)}" for book, distance in results
    )

    try:
        answer = AskResponse.model_validate_json(ask_model(
            ANSWER_PROMPT,
            f"Question: {ask.question}\n\nBooks:\n{books_text}"
        ))
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modeli ktheu pergjigje te pavlefshme"
        )

    # Hapi 5 - cdo id qe nuk ishte te librat e gjetur hidhet poshte
    retrieved_ids = [book.id for book, distance in results]
    answer.book_ids = [
        book_id for book_id in answer.book_ids if book_id in retrieved_ids
    ]

    return answer
