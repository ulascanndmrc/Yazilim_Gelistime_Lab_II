from fastapi import HTTPException, Header
from typing import Optional
from app.config import settings


def verify_internal_key(x_internal_api_key: Optional[str] = Header(None)) -> None:
    """Dependency: reject requests that don't carry the internal API key."""
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Forbidden: direct access not allowed")
