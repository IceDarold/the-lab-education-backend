from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
import fastapi.responses

from src.core.config import settings
from src.core.security import get_current_user, get_current_admin
from src.schemas.lesson import LessonCompleteResponse, LessonContent
from src.schemas.user import User
from src.services.ulf_parser import ULFParseError, parse_lesson_file, parse_lesson_file_from_text
from src.services.file_system_service import FileSystemService
from src.services.ulf_parser_service import ULFParserService
from src.services.content_scanner_service import ContentScannerService

router = APIRouter()


def _content_root() -> Path:
    return Path(settings.CONTENT_ROOT)


def _find_lesson_file(slug: str) -> Path:
    root = _content_root()
    if not root.exists():
        raise FileNotFoundError(root)

    direct = root / f"{slug}.lesson"
    if direct.exists():
        return direct

    matches = list(root.glob(f"**/{slug}.lesson"))
    if not matches:
        raise FileNotFoundError(slug)
    return matches[0]


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
async def get_lesson_raw(slug: str, current_admin: User = Depends(get_current_admin)) -> str:
    del current_admin
    fs_service = FileSystemService()
    try:
        lesson_path = _find_lesson_file(slug)
        relative_path = str(lesson_path.relative_to(Path(settings.CONTENT_ROOT)))
        return await fs_service.readFile(relative_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found") from None


@router.put("/{slug}/raw")
async def update_lesson_raw(slug: str, content: str, current_admin: User = Depends(get_current_admin)) -> dict:
    del current_admin
    fs_service = FileSystemService()
    ulf_service = ULFParserService()
    cs_service = ContentScannerService(fs_service)
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
        await fs_service.writeFile(relative_path, content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lesson file",
        ) from exc

    cs_service.clear_cache()
    return {"message": "Lesson updated successfully"}


async def _finalize(result: Any) -> Any:
    execute = getattr(result, "execute", None)
    if callable(execute):
        result = execute()
    if hasattr(result, "__await__"):
        result = await result
    return result


@router.post("/{lesson_id}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(lesson_id: str, current_user: User = Depends(get_current_user)) -> LessonCompleteResponse:
    from src.db.session import get_supabase_client  # local import to avoid circular dependency

    supabase = get_supabase_client()

    progress_payload = {
        "user_id": str(current_user.user_id),
        "lesson_id": lesson_id,
        "status": "completed",
    }

    upsert_action = supabase.table("user_lesson_progress").upsert(progress_payload)
    await _finalize(upsert_action)

    rpc_payload = {
        "lesson_id": lesson_id,
        "user_id": str(current_user.user_id),
    }

    rpc_response = await _finalize(supabase.rpc("calculate_course_progress", rpc_payload))
    rpc_data = getattr(rpc_response, "data", rpc_response) or {}

    new_percent = rpc_data.get("new_course_progress_percent")
    if new_percent is None:
        new_percent = rpc_data.get("progress_percent", 0)

    return LessonCompleteResponse(new_course_progress_percent=int(new_percent))

