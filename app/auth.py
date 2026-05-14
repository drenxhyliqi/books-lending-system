import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")


async def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key e gabuar!"
        )
