from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

from fastapi import Request

def get_auth_header(request: Request):
    return request.headers.get("Authorization", get_remote_address(request))

limiter = Limiter(
    key_func=get_auth_header,
    storage_uri="memory://"
)
