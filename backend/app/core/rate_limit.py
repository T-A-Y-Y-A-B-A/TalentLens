from slowapi import Limiter
from slowapi.util import get_remote_address

# Using in-memory fallback for now, in prod this should use redis
# e.g., default_limits=["200 per day", "50 per hour"]
limiter = Limiter(key_func=get_remote_address)
