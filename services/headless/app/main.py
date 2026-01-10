import os
from fastapi import FastAPI

app = FastAPI()

# Load environment variables (not used yet, but ready for MongoDB Atlas)
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "app")


@app.get("/health")
async def health():
    return {"status": "ok"}
