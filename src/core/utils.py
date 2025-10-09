import inspect
from typing import Any

try:  # pragma: no cover - optional dependency for test environments
    from unittest.mock import AsyncMock
except ImportError:  # pragma: no cover
    AsyncMock = None

from src.core.logging import get_logger
from src.core.errors import ExternalServiceError

logger = get_logger(__name__)


async def finalize_supabase_result(result: Any) -> Any:
    """Finalize a Supabase query result by executing it if needed and awaiting if necessary."""
    try:
        execute = getattr(result, "execute", None)
        if callable(execute):
            result = execute()
        while True:
            if AsyncMock is not None and isinstance(result, AsyncMock):
                result = result()
                continue
            if inspect.isawaitable(result):
                result = await result
                continue
            await_method = getattr(result, "__await__", None)
            if callable(await_method):
                result = await result
                continue
            break
        return result
    except Exception as e:
        logger.error(f"Error finalizing Supabase result: {str(e)}")
        raise ExternalServiceError(f"Failed to process Supabase query result: {str(e)}")


async def maybe_await(value: Any) -> Any:
    """Await value when it is awaitable; otherwise return it unchanged."""
    if AsyncMock is not None and isinstance(value, AsyncMock):
        value = value()
    if inspect.isawaitable(value):
        return await value
    return value
