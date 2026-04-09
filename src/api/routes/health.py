from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.session import get_db_session

router = APIRouter(tags=["system"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Return a stable liveness payload for the service."""
    return {"status": "ok"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
def readiness_check(
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    """Return readiness only when the database is reachable."""
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - safety net for readiness failures
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database is not ready",
        ) from exc
    return {"status": "ready", "database": "ok"}
