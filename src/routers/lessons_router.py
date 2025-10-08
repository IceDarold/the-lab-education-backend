from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.services.progress_service import ProgressService
from src.services.ulf_parser_service import ULFParserService
from src.services.file_system_service import FileSystemService
from src.services.content_scanner_service import ContentScannerService
from src.schemas import LessonCompleteRequest
from src.dependencies import get_db, get_current_user
from src.models.enrollment import Enrollment
from src.models.user import User

router = APIRouter()

@router.get("/{slug}")
async def get_lesson(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ulf_parser_service: ULFParserService = Depends(),
    file_system_service: FileSystemService = Depends(),
):
    # Derive course_slug and lesson_slug from slug (assuming format: course_slug/lesson_slug)
    parts = slug.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid lesson slug format")
    course_slug, lesson_slug = parts

    # Check enrollment
    enrollment_query = select(Enrollment).where(
        Enrollment.user_id == current_user.id,
        Enrollment.course_slug == course_slug
    )
    enrollment = await db.execute(enrollment_query)
    enrollment = enrollment.first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="User not enrolled in this course")

    # Read and parse the lesson file
    lesson_content = await file_system_service.read_file(f"content/courses/{course_slug}/{lesson_slug}.lesson")
    lesson_json = await ulf_parser_service.parse(lesson_content)
    return lesson_json

@router.post("/{slug}/complete")
async def complete_lesson(
    slug: str,
    request: LessonCompleteRequest,
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(),
    content_scanner_service: ContentScannerService = Depends(),
):
    course_slug = request.course_slug

    # Mark lesson as complete
    await progress_service.mark_lesson_as_complete(
        user_id=current_user.id,
        course_slug=course_slug,
        lesson_slug=slug
    )

    # Get next lesson slug
    lessons = await content_scanner_service.get_course_lesson_slugs(course_slug)
    try:
        index = lessons.index(slug)
        next_slug = lessons[index + 1] if index + 1 < len(lessons) else None
    except ValueError:
        next_slug = None

    return {"nextLessonSlug": next_slug}