import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar
from contextlib import asynccontextmanager

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pybreaker import CircuitBreaker, CircuitBreakerError
from supabase import Client
from supabase.lib.client_options import ClientOptions

from src.core.config import settings
from src.core.logging import get_logger
from src.core.errors import ExternalServiceError

logger = get_logger(__name__)

# Circuit breaker configuration
SUPABASE_CIRCUIT_BREAKER = CircuitBreaker(
    fail_max=5,  # Number of failures before opening circuit
    reset_timeout=60,  # Seconds to wait before trying again
    name="supabase_circuit_breaker"
)

# Timeout configuration
SUPABASE_TIMEOUT = 30  # seconds

T = TypeVar('T')


class SupabaseClientError(Exception):
    """Base exception for Supabase client errors."""
    pass


class SupabaseTimeoutError(SupabaseClientError):
    """Raised when Supabase operations timeout."""
    pass


class SupabaseCircuitBreakerError(SupabaseClientError):
    """Raised when circuit breaker is open."""
    pass


def is_network_error(exception: Exception) -> bool:
    """Check if exception is a network-related error that should be retried."""
    error_str = str(exception).lower()
    return any(keyword in error_str for keyword in [
        'connection', 'timeout', 'network', 'unreachable', 'dns',
        'connection reset', 'connection refused', 'connection aborted'
    ])


def retry_on_network_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to retry Supabase operations on network errors."""
    def retry_condition(exception):
        return (isinstance(exception, (ConnectionError, TimeoutError, OSError)) or
                is_network_error(exception))

    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_condition,
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying Supabase operation after failure: {retry_state.outcome.exception}. "
            f"Attempt {retry_state.attempt_number}/3"
        ),
        reraise=True
    )
    async def async_wrapper(*args, **kwargs) -> T:
        return await func(*args, **kwargs)

    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_condition,
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying Supabase operation after failure: {retry_state.outcome.exception}. "
            f"Attempt {retry_state.attempt_number}/3"
        ),
        reraise=True
    )
    def sync_wrapper(*args, **kwargs) -> T:
        return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


@asynccontextmanager
async def timeout_context(seconds: int):
    """Context manager for timeout handling."""
    try:
        yield await asyncio.wait_for(asyncio.sleep(0), timeout=seconds)
    except asyncio.TimeoutError:
        raise SupabaseTimeoutError(f"Operation timed out after {seconds} seconds")


class ResilientSupabaseClient:
    """A resilient Supabase client with retry logic, circuit breaker, and timeout handling."""

    def __init__(self, url: str, key: str, is_admin: bool = False):
        self.url = url
        self.key = key
        self.is_admin = is_admin
        self._client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Get or create the Supabase client."""
        if self._client is None:
            options = ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )
            self._client = Client(self.url, self.key, options)
        return self._client

    def _wrap_operation(self, operation_name: str):
        """Decorator to wrap Supabase operations with circuit breaker and error handling."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                try:
                    # Apply circuit breaker
                    result = await SUPABASE_CIRCUIT_BREAKER.call_async(
                        self._execute_with_timeout,
                        operation_name,
                        func,
                        *args,
                        **kwargs
                    )
                    return result
                except CircuitBreakerError:
                    logger.error(f"Circuit breaker is open for Supabase operation: {operation_name}")
                    raise SupabaseCircuitBreakerError("Supabase service is currently unavailable")
                except Exception as e:
                    logger.error(f"Supabase operation '{operation_name}' failed: {str(e)}")
                    raise ExternalServiceError(f"Supabase operation failed: {str(e)}")

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                try:
                    # Apply circuit breaker
                    result = SUPABASE_CIRCUIT_BREAKER.call(
                        self._execute_with_timeout_sync,
                        operation_name,
                        func,
                        *args,
                        **kwargs
                    )
                    return result
                except CircuitBreakerError:
                    logger.error(f"Circuit breaker is open for Supabase operation: {operation_name}")
                    raise SupabaseCircuitBreakerError("Supabase service is currently unavailable")
                except Exception as e:
                    logger.error(f"Supabase operation '{operation_name}' failed: {str(e)}")
                    raise ExternalServiceError(f"Supabase operation failed: {str(e)}")

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    async def _execute_with_timeout(self, operation_name: str, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute operation with timeout."""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=SUPABASE_TIMEOUT
                )
            else:
                # For sync functions, run in thread pool
                import concurrent.futures
                import threading
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(executor, func, *args, **kwargs),
                        timeout=SUPABASE_TIMEOUT
                    )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Supabase operation '{operation_name}' timed out after {SUPABASE_TIMEOUT} seconds")
            raise SupabaseTimeoutError(f"Operation timed out after {SUPABASE_TIMEOUT} seconds")

    def _execute_with_timeout_sync(self, operation_name: str, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute sync operation with timeout."""
        import signal

        def timeout_handler(signum, frame):
            raise SupabaseTimeoutError(f"Operation timed out after {SUPABASE_TIMEOUT} seconds")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SUPABASE_TIMEOUT)

        try:
            return func(*args, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    @property
    def auth(self):
        """Access to auth operations."""
        return self._AuthOperations(self)

    @property
    def table(self):
        """Access to table operations."""
        return self._TableOperations(self)

    @property
    def admin(self):
        """Access to admin operations."""
        return self._AdminOperations(self)

    class _AuthOperations:
        def __init__(self, client: 'ResilientSupabaseClient'):
            self._client = client

        @retry_on_network_errors
        def sign_in_with_password(self, credentials: dict) -> Any:
            return self._client._get_client().auth.sign_in_with_password(credentials)

        @retry_on_network_errors
        def sign_up(self, credentials: dict) -> Any:
            return self._client._get_client().auth.sign_up(credentials)

        @retry_on_network_errors
        def reset_password_for_email(self, email: str) -> Any:
            return self._client._get_client().auth.reset_password_for_email(email)

        @retry_on_network_errors
        def verify_otp(self, type: str, token: str) -> Any:
            return self._client._get_client().auth.verify_otp(type=type, token=token)

        @retry_on_network_errors
        def update_user(self, data: dict) -> Any:
            return self._client._get_client().auth.update_user(data)

    class _TableOperations:
        def __init__(self, client: 'ResilientSupabaseClient'):
            self._client = client

        def __call__(self, table_name: str):
            return self._TableInstance(self._client, table_name)

    class _TableInstance:
        def __init__(self, client: 'ResilientSupabaseClient', table_name: str):
            self._client = client
            self._table_name = table_name

        @retry_on_network_errors
        def select(self, *columns):
            query = self._client._get_client().table(self._table_name).select(*columns)
            return query

        @retry_on_network_errors
        def insert(self, data: dict):
            query = self._client._get_client().table(self._table_name).insert(data)
            return query

        @retry_on_network_errors
        def update(self, data: dict):
            query = self._client._get_client().table(self._table_name).update(data)
            return query

        @retry_on_network_errors
        def delete(self):
            query = self._client._get_client().table(self._table_name).delete()
            return query

    class _AdminOperations:
        def __init__(self, client: 'ResilientSupabaseClient'):
            self._client = client

        @retry_on_network_errors
        def delete_user(self, user_id: str) -> Any:
            return self._client._get_client().admin.delete_user(user_id)


# Global client instances
_supabase_client: Optional[ResilientSupabaseClient] = None
_supabase_admin_client: Optional[ResilientSupabaseClient] = None


def get_resilient_supabase_client() -> ResilientSupabaseClient:
    """Get resilient Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        _supabase_client = ResilientSupabaseClient(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
            is_admin=False
        )
    return _supabase_client


def get_resilient_supabase_admin_client() -> ResilientSupabaseClient:
    """Get resilient Supabase admin client instance."""
    global _supabase_admin_client
    if _supabase_admin_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
        _supabase_admin_client = ResilientSupabaseClient(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            is_admin=True
        )
    return _supabase_admin_client


async def check_supabase_health() -> dict:
    """Check Supabase connectivity and health."""
    try:
        client = get_resilient_supabase_client()
        # Try a simple operation to check connectivity
        # We'll use the auth endpoint to check if service is available
        # This is a lightweight check that doesn't require authentication

        # For health check, we can try to get the current session (should be None for health check)
        # But if that fails due to network issues, we know the service is down
        try:
            # This will fail with auth error but should not fail with network error
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client._get_client().auth.get_session()
            )
        except Exception as e:
            # If it's an auth error, service is up. If network error, service is down.
            if "auth" in str(e).lower() or "unauthorized" in str(e).lower():
                return {"status": "healthy", "message": "Supabase service is responding"}
            else:
                raise e

        return {"status": "healthy", "message": "Supabase service is responding"}

    except SupabaseCircuitBreakerError:
        return {"status": "degraded", "message": "Circuit breaker is open - service temporarily unavailable"}
    except SupabaseTimeoutError:
        return {"status": "unhealthy", "message": "Supabase service timeout"}
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        return {"status": "unhealthy", "message": f"Supabase service error: {str(e)}"}