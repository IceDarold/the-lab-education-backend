class ContentFileNotFoundError(Exception):
    """Raised when a content file is not found in the file system."""
    pass


class SecurityError(Exception):
    """Raised when a security violation occurs in file system operations."""
    pass


class ParsingError(Exception):
    """Raised when parsing fails."""
    pass
class FileSystemOperationError(Exception):
    """Raised when file system operations fail unexpectedly."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(Exception):
    """Raised when external service calls fail."""
    pass


class SupabaseClientError(Exception):
    """Base exception for Supabase client errors."""
    pass


class SupabaseTimeoutError(SupabaseClientError):
    """Raised when Supabase operations timeout."""
    pass


class SupabaseCircuitBreakerError(SupabaseClientError):
    """Raised when circuit breaker is open."""
    pass


class SupabaseNetworkError(SupabaseClientError):
    """Raised when Supabase network operations fail."""
    pass