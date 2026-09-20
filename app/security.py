from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

limiter = Limiter(key_func=get_remote_address)


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.APP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
