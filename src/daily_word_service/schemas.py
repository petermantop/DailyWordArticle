from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class Article(BaseModel):
    header: str = Field(..., min_length=1, max_length=60)
    body: str = Field(..., min_length=1, max_length=300)


class HealthResponse(BaseModel):
    status: HealthStatus
    cache_ready: bool
    scheduler_enabled: bool
    last_refresh_at: str | None
    last_error: str | None
