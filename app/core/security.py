from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings, Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    api_key: str | None = Security(api_key_header), settings: Settings = Depends(get_settings)
) -> str:
    if not api_key or api_key != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key

