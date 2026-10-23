from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.api.routes import router
from app.config import settings
from app.db import SessionLocal, get_db, init_db
from app.schemas.schemas import HealthOut
from app.services.seed import seed_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_db(db)  # idempotent
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="XenMind - AI Agent Reliability Lab. Run seeded scenarios against a "
    "deterministic mock agent, persist ordered events and assertions, replay runs, "
    "and compare agent versions. No real external tools, no billing.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.lovable\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", response_model=HealthOut, tags=["health"])
def health(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthOut(status="ok", service="xenmind-backend", version=__version__, database=db_status)


@app.get("/", tags=["health"])
def root():
    return {
        "service": "xenmind-backend",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
