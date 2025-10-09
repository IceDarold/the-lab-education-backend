import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.services.progress_service import ProgressService
from src.models.user_lesson_progress import UserLessonProgress
from src.models.user_activity_log import UserActivityLog
from src.services.content_scanner_service import ContentScannerService


pytestmark = pytest.mark.asyncio


class TestProgressService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_content_service(self):
        return AsyncMock(spec=ContentScannerService)

    async def test_mark_lesson_as_complete_new_progress(self, mock_db):
        # Arrange
        user_id = 1
        course_slug = "python-basics"
        lesson_slug = "functions"

        # Mock no existing progress
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        await ProgressService.mark_lesson_as_complete(user_id, course_slug, lesson_slug, mock_db)

        # Assert
        # Should add new UserLessonProgress
        assert mock_db.add.call_count == 2  # Progress and ActivityLog
        mock_db.commit.assert_called_once()

        # Check UserLessonProgress creation
        progress_call = mock_db.add.call_args_list[0][0][0]
        assert isinstance(progress_call, UserLessonProgress)
        assert progress_call.user_id == user_id
        assert progress_call.course_slug == course_slug
        assert progress_call.lesson_slug == lesson_slug
        assert isinstance(progress_call.completion_date, datetime)

        # Check UserActivityLog creation
        activity_call = mock_db.add.call_args_list[1][0][0]
        assert isinstance(activity_call, UserActivityLog)
        assert activity_call.user_id == user_id
        assert activity_call.activity_type == 'LESSON_COMPLETED'
        assert activity_call.details == {'lesson_slug': lesson_slug, 'course_slug': course_slug}

    async def test_mark_lesson_as_complete_update_existing_progress(self, mock_db):
        # Arrange
        user_id = 1
        course_slug = "python-basics"
        lesson_slug = "functions"

        # Mock existing progress
        existing_progress = MagicMock(spec=UserLessonProgress)
        existing_progress.completion_date = datetime(2023, 1, 1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_progress

        # Act
        await ProgressService.mark_lesson_as_complete(user_id, course_slug, lesson_slug, mock_db)

        # Assert
        # Should update existing progress and add activity log
        assert mock_db.add.call_count == 1  # Only ActivityLog, progress is updated
        mock_db.commit.assert_called_once()

        # Check completion_date was updated
        assert existing_progress.completion_date != datetime(2023, 1, 1)

        # Check UserActivityLog creation
        activity_call = mock_db.add.call_args_list[0][0][0]
        assert isinstance(activity_call, UserActivityLog)
        assert activity_call.user_id == user_id
        assert activity_call.activity_type == 'LESSON_COMPLETED'
        assert activity_call.details == {'lesson_slug': lesson_slug, 'course_slug': course_slug}

    async def test_get_user_progress_for_course(self, mock_db, mock_content_service):
        # Arrange
        user_id = 1
        course_slug = "python-basics"

        # Mock content service
        lesson_slugs = ["functions", "loops", "classes"]
        mock_content_service.get_course_lesson_slugs.return_value = lesson_slugs

        # Mock completed lessons
        mock_result = MagicMock()
        mock_result.lesson_slug = "functions"
        mock_db.execute.return_value = [mock_result]  # One completed lesson

        # Act
        result = await ProgressService.get_user_progress_for_course(user_id, course_slug, mock_db, mock_content_service)

        # Assert
        assert result['completed'] == 1
        assert result['total'] == 3
        assert result['percentage'] == pytest.approx(33.333333333333336)  # 1/3 * 100

        mock_content_service.get_course_lesson_slugs.assert_called_once_with(course_slug)

    async def test_get_user_progress_for_course_all_completed(self, mock_db, mock_content_service):
        # Arrange
        user_id = 1
        course_slug = "python-basics"

        # Mock content service
        lesson_slugs = ["functions", "loops"]
        mock_content_service.get_course_lesson_slugs.return_value = lesson_slugs

        # Mock completed lessons
        mock_results = [
            MagicMock(lesson_slug="functions"),
            MagicMock(lesson_slug="loops")
        ]
        mock_db.execute.return_value = mock_results

        # Act
        result = await ProgressService.get_user_progress_for_course(user_id, course_slug, mock_db, mock_content_service)

        # Assert
        assert result['completed'] == 2
        assert result['total'] == 2
        assert result['percentage'] == 100.0

    async def test_get_user_progress_for_course_none_completed(self, mock_db, mock_content_service):
        # Arrange
        user_id = 1
        course_slug = "python-basics"

        # Mock content service
        lesson_slugs = ["functions", "loops"]
        mock_content_service.get_course_lesson_slugs.return_value = lesson_slugs

        # Mock no completed lessons
        mock_db.execute.return_value = []

        # Act
        result = await ProgressService.get_user_progress_for_course(user_id, course_slug, mock_db, mock_content_service)

        # Assert
        assert result['completed'] == 0
        assert result['total'] == 2
        assert result['percentage'] == 0.0

    async def test_get_user_progress_for_course_empty_course(self, mock_db, mock_content_service):
        # Arrange
        user_id = 1
        course_slug = "empty-course"

        # Mock content service - empty course
        lesson_slugs = []
        mock_content_service.get_course_lesson_slugs.return_value = lesson_slugs

        # Mock no completed lessons
        mock_db.execute.return_value = []

        # Act
        result = await ProgressService.get_user_progress_for_course(user_id, course_slug, mock_db, mock_content_service)

        # Assert
        assert result['completed'] == 0
        assert result['total'] == 0
        assert result['percentage'] == 0.0

    async def test_get_user_progress_for_course_partial_completion(self, mock_db, mock_content_service):
        # Arrange
        user_id = 1
        course_slug = "python-basics"

        # Mock content service
        lesson_slugs = ["functions", "loops", "classes", "inheritance"]
        mock_content_service.get_course_lesson_slugs.return_value = lesson_slugs

        # Mock completed lessons
        mock_results = [
            MagicMock(lesson_slug="functions"),
            MagicMock(lesson_slug="classes")
        ]
        mock_db.execute.return_value = mock_results

        # Act
        result = await ProgressService.get_user_progress_for_course(user_id, course_slug, mock_db, mock_content_service)

        # Assert
        assert result['completed'] == 2
        assert result['total'] == 4
        assert result['percentage'] == 50.0
