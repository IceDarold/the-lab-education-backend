from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from uuid import UUID
from src.models.user_lesson_progress import UserLessonProgress
from src.models.user_activity_log import UserActivityLog
from src.services.content_scanner_service import ContentScannerService
from src.core.errors import DatabaseError, ValidationError
from src.core.logging import get_logger
from src.core.utils import maybe_await

# Ensure SQLAlchemy relationship dependencies are registered for mapped models
from src.models import user as _user_model  # noqa: F401
from src.models import enrollment as _enrollment_model  # noqa: F401

logger = get_logger(__name__)


class ProgressService:
    @staticmethod
    async def mark_lesson_as_complete(user_id: UUID, course_slug: str, lesson_slug: str, db: AsyncSession) -> None:
        logger.info(f"Marking lesson as complete: user={user_id}, course={course_slug}, lesson={lesson_slug}")
        try:
            # Validate inputs
            if not course_slug or not lesson_slug:
                raise ValidationError("Course slug and lesson slug are required")

            # Check if UserLessonProgress exists
            stmt = select(UserLessonProgress).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.course_slug == course_slug,
                UserLessonProgress.lesson_slug == lesson_slug
            )
            result = await db.execute(stmt)
            progress = await maybe_await(result.scalar_one_or_none())

            if progress is None:
                # Create new progress record
                logger.debug(f"Creating new progress record for user {user_id}")
                progress = UserLessonProgress(
                    user_id=user_id,
                    course_slug=course_slug,
                    lesson_slug=lesson_slug,
                    completion_date=datetime.now()
                )
                db.add(progress)
            else:
                # Update existing completion_date
                logger.debug(f"Updating existing progress record for user {user_id}")
                progress.completion_date = datetime.now()

            # Create UserActivityLog
            activity_log = UserActivityLog(
                user_id=user_id,
                activity_type='LESSON_COMPLETED',
                details={'lesson_slug': lesson_slug, 'course_slug': course_slug}
            )
            db.add(activity_log)

            # Commit all changes
            await db.commit()
            logger.info(f"Successfully marked lesson as complete for user {user_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error marking lesson complete for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Failed to update lesson progress: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error marking lesson complete for user {user_id}: {str(e)}")
            await db.rollback()
            raise DatabaseError(f"Unexpected error during progress update: {str(e)}")

    @staticmethod
    async def get_user_progress_for_course(user_id: UUID, course_slug: str, db: AsyncSession, content_service: ContentScannerService) -> dict:
        logger.debug(f"Getting progress for user {user_id} in course {course_slug}")
        try:
            # Validate inputs
            if not course_slug:
                raise ValidationError("Course slug is required")

            # Get lesson slugs from content service
            lesson_slugs = await content_service.get_course_lesson_slugs(course_slug)

            # Query completed lessons
            stmt = select(UserLessonProgress.lesson_slug).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.course_slug == course_slug
            )
            result = await db.execute(stmt)
            completed_slugs = [row.lesson_slug for row in result]

            # Calculate stats
            completed = len(completed_slugs)
            total = len(lesson_slugs)
            percentage = (completed / total * 100) if total > 0 else 0.0

            logger.debug(f"Progress calculated: {completed}/{total} ({percentage:.1f}%) for user {user_id}")
            return {
                'completed': completed,
                'total': total,
                'percentage': percentage
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting progress for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve progress: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting progress for user {user_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error during progress retrieval: {str(e)}")
