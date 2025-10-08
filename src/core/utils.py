from typing import Any


async def finalize_supabase_result(result: Any) -> Any:
    """Finalize a Supabase query result by executing it if needed and awaiting if necessary."""
    execute = getattr(result, "execute", None)
    if callable(execute):
        result = execute()
    if hasattr(result, "__await__"):
        result = await result
    return result