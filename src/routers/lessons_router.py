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
from src.core.errors import ValidationError, DatabaseError, ContentFileNotFoundError, ParsingError
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/{slug}")
async def get_lesson(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ulf_parser_service: ULFParserService = Depends(),
    file_system_service: FileSystemService = Depends(),
):
    logger.info(f"User {current_user.email} requesting lesson: {slug}")

    try:
        # Derive course_slug and lesson_slug from slug (assuming format: course_slug/lesson_slug)
        parts = slug.split("/", 1)
        if len(parts) != 2:
            logger.warning(f"Invalid lesson slug format: {slug} for user {current_user.email}")
            raise ValidationError("Invalid lesson slug format. Expected format: course_slug/lesson_slug")

        course_slug, lesson_slug = parts
        logger.debug(f"Parsed slug - course: {course_slug}, lesson: {lesson_slug}")

        # Check enrollment
        try:
            enrollment_query = select(Enrollment).where(
                Enrollment.user_id == current_user.id,
                Enrollment.course_slug == course_slug
            )
            enrollment_result = await db.execute(enrollment_query)
            enrollment = enrollment_result.first()

            if not enrollment:
                logger.warning(f"User {current_user.email} not enrolled in course {course_slug}")
                raise HTTPException(
                    status_code=403,
                    detail=f"You are not enrolled in the course '{course_slug}'. Please enroll first to access lessons."
                )

        except Exception as e:
            logger.error(f"Database error checking enrollment for user {current_user.email} in course {course_slug}: {str(e)}")
            raise DatabaseError(f"Failed to verify course enrollment: {str(e)}")

        # Read and parse the lesson file
        try:
            lesson_path = f"content/courses/{course_slug}/{lesson_slug}.lesson"
            logger.debug(f"Reading lesson file: {lesson_path}")
            lesson_content = await file_system_service.read_file(lesson_path)

        except ContentFileNotFoundError:
            logger.warning(f"Lesson file not found: {lesson_path} for user {current_user.email}")
            raise HTTPException(
                status_code=404,
                detail=f"Lesson '{lesson_slug}' not found in course '{course_slug}'. The lesson may not exist or may have been moved."
            )
        except Exception as e:
            logger.error(f"File system error reading lesson {lesson_path}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Unable to access lesson content. Please try again later."
            )

        # Parse the lesson content
        try:
            logger.debug(f"Parsing lesson content for {lesson_path}")
            lesson_json = ulf_parser_service.parse(lesson_content)

        except ParsingError as e:
            logger.error(f"Parsing error for lesson {lesson_path}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Lesson content is corrupted or in an invalid format. Please contact support with lesson: {slug}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing lesson {lesson_path}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process lesson content. Please try again later."
            )

        logger.info(f"Successfully served lesson {slug} to user {current_user.email}")
        return lesson_json

    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error for lesson request {slug}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error in lesson request {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error in lesson request {slug} for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")

@router.post("/{slug}/complete")
async def complete_lesson(
    slug: str,
    request: LessonCompleteRequest,
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(),
    content_scanner_service: ContentScannerService = Depends(),
):
    logger.info(f"User {current_user.email} completing lesson: {slug} in course: {request.course_slug}")

    try:
        course_slug = request.course_slug

        # Validate input
        if not course_slug or not slug:
            logger.warning(f"Invalid completion request - missing course_slug or lesson_slug for user {current_user.email}")
            raise ValidationError("Both course_slug and lesson_slug are required")

        # Mark lesson as complete
        try:
            logger.debug(f"Marking lesson {slug} as complete for user {current_user.email}")
            await progress_service.mark_lesson_as_complete(
                user_id=current_user.id,
                course_slug=course_slug,
                lesson_slug=slug
            )
            logger.info(f"Successfully marked lesson {slug} as complete for user {current_user.email}")

        except Exception as e:
            logger.error(f"Failed to mark lesson {slug} as complete for user {current_user.email}: {str(e)}")
            raise DatabaseError(f"Failed to update lesson progress: {str(e)}")

        # Get next lesson slug
        try:
            logger.debug(f"Retrieving lesson list for course {course_slug}")
            lessons = await content_scanner_service.get_course_lesson_slugs(course_slug)

            try:
                index = lessons.index(slug)
                next_slug = lessons[index + 1] if index + 1 < len(lessons) else None
                logger.debug(f"Next lesson for {slug} in course {course_slug}: {next_slug}")

            except ValueError:
                logger.warning(f"Lesson {slug} not found in course {course_slug} lesson list for user {current_user.email}")
                next_slug = None

        except Exception as e:
            logger.error(f"Failed to retrieve course lessons for {course_slug}: {str(e)}")
            # Don't fail the completion if we can't get next lesson, just log and continue
            next_slug = None

        logger.info(f"Lesson completion successful for user {current_user.email}, next lesson: {next_slug}")
        return {"nextLessonSlug": next_slug}

    except ValidationError as e:
        logger.warning(f"Validation error in lesson completion for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error in lesson completion for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save lesson progress. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error in lesson completion for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while completing the lesson. Please try again.")