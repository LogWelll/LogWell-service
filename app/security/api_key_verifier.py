from fastapi import HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from settings import settings

api_key_header = APIKeyHeader(name="x-API-key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in settings.allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
        )
