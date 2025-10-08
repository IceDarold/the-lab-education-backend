from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from src.models.user_lesson_progress import UserLessonProgress
from src.models.user_activity_log import UserActivityLog
from src.services.content_scanner_service import ContentScannerService


class ProgressService:
    @staticmethod
    async def mark_lesson_as_complete(user_id: int, course_slug: str, lesson_slug: str, db: AsyncSession) -> None:
        # Check if UserLessonProgress exists
        stmt = select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.course_slug == course_slug,
            UserLessonProgress.lesson_slug == lesson_slug
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress is None:
            # Create new progress record
            progress = UserLessonProgress(
                user_id=user_id,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
                completion_date=datetime.now()
            )
            db.add(progress)
        else:
            # Update existing completion_date
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

    @staticmethod
    async def get_user_progress_for_course(user_id: int, course_slug: str, db: AsyncSession, content_service: ContentScannerService) -> dict:
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

        return {
            'completed': completed,
            'total': total,
            'percentage': percentage
        }