from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
import fastapi.responses

from src.core.config import settings
from src.core.security import get_current_user, get_current_admin
from src.core.utils import finalize_supabase_result
from src.dependencies import get_fs_service, get_ulf_parser, get_content_scanner, validate_content_size
from src.schemas.lesson import LessonCompleteResponse, LessonContent
from src.schemas.user import User
from src.services.ulf_parser import ULFParseError, parse_lesson_file, parse_lesson_file_from_text
from src.services.file_system_service import FileSystemService
from src.services.ulf_parser_service import ULFParserService
from src.services.content_scanner_service import ContentScannerService

router = APIRouter()

# Cache for lesson file paths to avoid repeated searches
_lesson_path_cache: dict[str, Path] = {}


def _clear_lesson_path_cache():
    """Clear the lesson path cache when content is updated."""
    _lesson_path_cache.clear()


def _content_root() -> Path:
    return Path(settings.CONTENT_ROOT)


def _find_lesson_file(slug: str) -> Path:
    # Check cache first
    if slug in _lesson_path_cache:
        cached_path = _lesson_path_cache[slug]
        if cached_path.exists():
            return cached_path
        else:
            # Cache is stale, remove it
            del _lesson_path_cache[slug]

    root = _content_root()
    if not root.exists():
        raise FileNotFoundError(root)

    # Search with limited depth: assume lessons are in courses/course_slug/lesson_slug.lesson
    matches = list(root.glob(f"courses/*/{slug}.lesson"))
    if not matches:
        # Fallback to deeper search if not found (for future extensibility)
        matches = list(root.glob(f"**/{slug}.lesson"))
        if not matches:
            raise FileNotFoundError(slug)

    found_path = matches[0]
    # Cache the result
    _lesson_path_cache[slug] = found_path
    return found_path


@router.get("/{slug}", response_model=LessonContent)
async def get_lesson_content(slug: str, current_user: User = Depends(get_current_user)) -> LessonContent:
    del current_user
    try:
        lesson_path = _find_lesson_file(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found") from None

    try:
        return parse_lesson_file(lesson_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found") from None
    except ULFParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{slug}/raw", response_class=fastapi.responses.PlainTextResponse)
async def get_lesson_raw(slug: str, current_admin: User = Depends(get_current_admin), fs_service: FileSystemService = Depends(get_fs_service)) -> str:
    del current_admin
    try:
        lesson_path = _find_lesson_file(slug)
        relative_path = str(lesson_path.relative_to(Path(settings.CONTENT_ROOT)))
        return await fs_service.read_file(relative_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found") from None


@router.put("/{slug}/raw")
async def update_lesson_raw(slug: str, content: str = Body(..., media_type="text/plain"), current_admin: User = Depends(get_current_admin), fs_service: FileSystemService = Depends(get_fs_service), ulf_service: ULFParserService = Depends(get_ulf_parser), cs_service: ContentScannerService = Depends(get_content_scanner)) -> dict:
    del current_admin

    # Validate content size
    validate_content_size(content)

    try:
        lesson_path = _find_lesson_file(slug)
        relative_path = str(lesson_path.relative_to(Path(settings.CONTENT_ROOT)))
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found") from None

    # Validate by attempting to parse
    try:
        ulf_service.parse(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid lesson format: {str(exc)}",
        ) from exc

    # Overwrite the file
    try:
        await fs_service.write_file(relative_path, content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lesson file",
        ) from exc

    cs_service.clear_cache()
    _clear_lesson_path_cache()
    return {"message": "Lesson updated successfully"}


@router.post("/{lesson_id}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(lesson_id: str, current_user: User = Depends(get_current_user)) -> LessonCompleteResponse:
    from src.db.session import get_supabase_client  # local import to avoid circular dependency

    supabase = get_supabase_client()

    # Validate lesson_id format: must contain exactly one '/' and both parts non-empty
    if '/' not in lesson_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lesson_id format. Expected 'course_slug/lesson_slug'."
        )
    parts = lesson_id.split('/', 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lesson_id format. Expected 'course_slug/lesson_slug'."
        )
    course_slug, lesson_slug = parts

    progress_payload = {
        "user_id": str(current_user.user_id),
        "course_slug": course_slug,
        "lesson_slug": lesson_slug,
        "status": "completed",
    }

    upsert_action = supabase.table("user_lesson_progress").upsert(progress_payload)
    await finalize_supabase_result(upsert_action)

    rpc_payload = {
        "lesson_id": lesson_id,
        "user_id": str(current_user.user_id),
    }

    rpc_response = await finalize_supabase_result(supabase.rpc("calculate_course_progress", rpc_payload))
    rpc_data = getattr(rpc_response, "data", rpc_response) or {}

    new_percent = rpc_data.get("new_course_progress_percent")
    if new_percent is None:
        new_percent = rpc_data.get("progress_percent", 0)

    return LessonCompleteResponse(new_course_progress_percent=int(new_percent))

