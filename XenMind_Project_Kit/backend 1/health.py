"""
Health endpoint: the simplest possible "is the server alive?" check.

The frontend, deployment platforms, and you (in a browser) can hit this
to confirm the API is up before anything else is wired.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    # This model IS the API contract. The frontend's TypeScript type should match it.
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )
