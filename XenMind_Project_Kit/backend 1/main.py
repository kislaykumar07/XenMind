"""
Entry point for the XenMind API.

Run from the backend/ folder:
    uvicorn app.main:app --reload

"app.main:app" means: in the package `app`, module `main`, use the object named `app`.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings


def create_app() -> FastAPI:
    """Build the FastAPI app. A factory function makes testing and config changes easier."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Agent Reliability Lab — Break it. Trace it. Trust it.",
    )

    # CORS: browsers block a page on localhost:5173 from calling localhost:8000
    # unless the API explicitly allows that origin. This is that permission.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Every route lives under /api so the frontend has one clear prefix.
    app.include_router(health.router, prefix="/api")

    return app


app = create_app()
