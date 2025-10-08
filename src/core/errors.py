class FileNotFoundError(Exception):
    """Raised when a file is not found in the file system."""
    pass


class SecurityError(Exception):
    """Raised when a security violation occurs in file system operations."""
    pass