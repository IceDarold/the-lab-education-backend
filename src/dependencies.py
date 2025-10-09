from src.db.session import get_db_session, get_db
from fastapi import Depends, HTTPException, status
from src.services.file_system_service import FileSystemService
from src.services.content_scanner_service import ContentScannerService
from src.services.ulf_parser_service import ULFParserService
from src.core.security import get_current_user, get_current_admin
from src.schemas.user import User


def get_fs_service() -> FileSystemService:
    return FileSystemService()


def get_content_scanner(fs: FileSystemService = Depends(get_fs_service)) -> ContentScannerService:
    return ContentScannerService(fs)


def get_ulf_parser() -> ULFParserService:
    return ULFParserService()


def require_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency wrapper for retrieving the current authenticated user."""
    return current_user


def require_current_admin(current_admin: User = Depends(get_current_admin)) -> User:
    """Dependency wrapper for retrieving the current authenticated admin."""
    return current_admin


def validate_content_size(content: str, max_size_mb: int = 10) -> str:
    """Validate content size to prevent large file uploads.

    Args:
        content: The content string to validate
        max_size_mb: Maximum allowed size in MB (default 10MB)

    Returns:
        The content if valid

    Raises:
        HTTPException: If content exceeds size limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    content_size = len(content.encode('utf-8'))

    if content_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Content size ({content_size} bytes) exceeds maximum allowed size ({max_size_bytes} bytes)"
        )

    return content


def validate_safe_path(path: str) -> str:
    """Validate path to prevent directory traversal attacks.

    Args:
        path: The path string to validate

    Returns:
        The path if valid

    Raises:
        HTTPException: If path contains traversal attempts
    """
    from pathlib import PurePosixPath

    if not path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path format"
        )

    # Reject absolute paths and drive-relative paths
    if path.startswith(("/", "\\")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    candidate = PurePosixPath(path.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return path
