from fastapi import FastAPI, status

app = FastAPI()


@app.get("/", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok", "library": "open"}
