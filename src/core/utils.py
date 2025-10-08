from typing import Any
from src.core.logging import get_logger
from src.core.errors import ExternalServiceError

logger = get_logger(__name__)


async def finalize_supabase_result(result: Any) -> Any:
    """Finalize a Supabase query result by executing it if needed and awaiting if necessary."""
    try:
        execute = getattr(result, "execute", None)
        if callable(execute):
            result = execute()
        if hasattr(result, "__await__"):
            result = await result
        return result
    except Exception as e:
        logger.error(f"Error finalizing Supabase result: {str(e)}")
        raise ExternalServiceError(f"Failed to process Supabase query result: {str(e)}")