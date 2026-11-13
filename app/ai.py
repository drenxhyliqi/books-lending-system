import os
from fastapi import HTTPException, status
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")


# Teksti i librit qe i dergohet OpenAI: titulli, pershkrimi, kategoria, autoret
def book_to_text(book) -> str:
    authors = ", ".join(author.full_name for author in book.authors)
    category = book.category.name if book.category else ""

    return (
        f"Title: {book.title}\n"
        f"Description: {book.description or ''}\n"
        f"Category: {category}\n"
        f"Authors: {authors}"
    )


# Embedding = liste numrash qe e perfaqeson kuptimin e tekstit
# Tekste me kuptim te ngjashem kane vektore te afert
def create_embedding(text: str) -> list[float]:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
        response = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text
        )
    except OpenAIError:
        # Perfshin edhe rastin kur mungon key, pa e shfaqur gabimin e OpenAI
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sherbimi AI nuk eshte i disponueshem per momentin"
        )

    return response.data[0].embedding


# system = rregullat per modelin, user = pyetja bashke me te dhenat
# Kthen tekst ne format JSON, routeri e validon me schema
# OpenAI kerkon qe fjala "JSON" te jete diku ne mesazhe kur perdoret json_object
def ask_model(system: str, user: str) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
        response = client.responses.create(
            model=OPENAI_CHAT_MODEL,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            text={"format": {"type": "json_object"}}
        )
    except OpenAIError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sherbimi AI nuk eshte i disponueshem per momentin"
        )

    return response.output_text
