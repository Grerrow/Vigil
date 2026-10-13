"""FastAPI application setup."""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load configuration before importing db, which reads DATABASE_PATH at import time.
load_dotenv()

from db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: make sure the DB tables exist."""
    init_db()
    yield


app = FastAPI(
    title="Vigil API",
    description="Real-time person detection and counting service.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Basic liveness check used during setup and by monitoring tools."""
    return {"status": "ok"}


from routes import detect, history
app.include_router(detect.router)
app.include_router(history.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
