from fastapi import HTTPException, status
from src.services.file_system_service import FileSystemService
from src.services.content_scanner_service import ContentScannerService
from src.services.ulf_parser_service import ULFParserService


def get_fs_service() -> FileSystemService:
    return FileSystemService()


def get_content_scanner(fs: FileSystemService = get_fs_service()) -> ContentScannerService:
    return ContentScannerService(fs)


def get_ulf_parser() -> ULFParserService:
    return ULFParserService()


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
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
    from pathlib import Path

    # Check for obvious traversal patterns
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path: directory traversal not allowed"
        )

    # Normalize path and check if it resolves to something outside allowed directory
    try:
        normalized = Path(path).resolve()
        # Basic check - ensure no absolute paths or traversal
        if str(normalized) != path.replace("\\", "/").replace("//", "/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path: path traversal detected"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path format"
        )

    return path