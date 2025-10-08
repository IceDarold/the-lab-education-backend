class ContentFileNotFoundError(Exception):
    """Raised when a content file is not found in the file system."""
    pass


class SecurityError(Exception):
    """Raised when a security violation occurs in file system operations."""
    pass


class ParsingError(Exception):
    """Raised when parsing fails."""
    pass