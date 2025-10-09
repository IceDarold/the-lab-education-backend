import asyncio
import time
from typing import Any, Dict, Optional
from threading import Lock
from src.core.logging import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and hasn't expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry['expires_at']:
                    logger.debug(f"Cache hit for key: {key}")
                    return entry['value']
                else:
                    # Expired, remove it
                    del self._cache[key]
                    logger.debug(f"Cache expired for key: {key}")
            logger.debug(f"Cache miss for key: {key}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in cache with TTL."""
        with self._lock:
            expires_at = time.time() + ttl_seconds
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
            logger.debug(f"Cached value for key: {key} with TTL: {ttl_seconds}s")

    def delete(self, key: str) -> None:
        """Delete a value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache entry for key: {key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.debug("Cleared all cache entries")


# Global cache instance
_user_cache = SimpleCache()


def get_user_cache() -> SimpleCache:
    """Get the global user cache instance."""
    return _user_cache


def cache_key_user_by_email(email: str) -> str:
    """Generate cache key for user lookup by email."""
    return f"user:email:{email}"


def cache_key_user_by_id(user_id: str) -> str:
    """Generate cache key for user lookup by ID."""
    return f"user:id:{user_id}"