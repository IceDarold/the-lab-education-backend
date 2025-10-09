from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from src.core.logging import get_logger

logger = get_logger(__name__)

# Create rate limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
LOGIN_RATE_LIMIT = "5/minute"  # 5 login attempts per minute per IP
REGISTER_RATE_LIMIT = "3/minute"  # 3 registration attempts per minute per IP
REFRESH_RATE_LIMIT = "10/minute"  # 10 token refresh attempts per minute per IP

def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key based on IP and endpoint"""
    client_ip = get_remote_address(request)
    endpoint = request.url.path
    return f"{client_ip}:{endpoint}"

# Custom rate limiter for auth endpoints
auth_limiter = Limiter(key_func=get_rate_limit_key)