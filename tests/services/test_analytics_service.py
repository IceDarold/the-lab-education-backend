import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import func
from src.services.analytics_service import AnalyticsService
from src.models.user_activity_log import UserActivityLog
from src.schemas import TrackEventRequest


pytestmark = pytest.mark.asyncio


class TestAnalyticsService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    async def test_get_activity_details_with_data(self, mock_db):
        # Arrange
        user_id = 1

        # Mock query results
        mock_row1 = MagicMock()
        mock_row1.date = datetime(2024, 10, 1).date()
        mock_row1.activity_type = 'LESSON_COMPLETED'
        mock_row1.count = 3

        mock_row2 = MagicMock()
        mock_row2.date = datetime(2024, 10, 1).date()
        mock_row2.activity_type = 'QUIZ_ATTEMPT'
        mock_row2.count = 1

        mock_row3 = MagicMock()
        mock_row3.date = datetime(2024, 10, 2).date()
        mock_row3.activity_type = 'LESSON_COMPLETED'
        mock_row3.count = 2

        mock_db.execute.return_value.all.return_value = [mock_row1, mock_row2, mock_row3]

        # Act
        result = await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        assert len(result) == 2

        # Check first date
        day1 = result[0]
        assert day1['date'] == '2024-10-01'
        assert day1['LESSON_COMPLETED'] == 3
        assert day1['QUIZ_ATTEMPT'] == 1

        # Check second date
        day2 = result[1]
        assert day2['date'] == '2024-10-02'
        assert day2['LESSON_COMPLETED'] == 2

        # Verify sorted by date
        assert result[0]['date'] < result[1]['date']

    async def test_get_activity_details_empty_result(self, mock_db):
        # Arrange
        user_id = 1
        mock_db.execute.return_value.all.return_value = []

        # Act
        result = await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        assert result == []

    async def test_get_activity_details_single_activity_type(self, mock_db):
        # Arrange
        user_id = 1

        mock_row = MagicMock()
        mock_row.date = datetime(2024, 10, 1).date()
        mock_row.activity_type = 'LOGIN'
        mock_row.count = 5

        mock_db.execute.return_value.all.return_value = [mock_row]

        # Act
        result = await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        assert len(result) == 1
        day = result[0]
        assert day['date'] == '2024-10-01'
        assert day['LOGIN'] == 5

    async def test_get_activity_details_multiple_dates(self, mock_db):
        # Arrange
        user_id = 1

        # Create mock rows for different dates
        rows = []
        dates = [datetime(2024, 9, 30).date(), datetime(2024, 10, 1).date(), datetime(2024, 9, 29).date()]

        for i, date in enumerate(dates):
            mock_row = MagicMock()
            mock_row.date = date
            mock_row.activity_type = 'LESSON_COMPLETED'
            mock_row.count = i + 1
            rows.append(mock_row)

        mock_db.execute.return_value.all.return_value = rows

        # Act
        result = await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        assert len(result) == 3

        # Verify sorted by date
        assert result[0]['date'] == '2024-09-29'
        assert result[1]['date'] == '2024-09-30'
        assert result[2]['date'] == '2024-10-01'

        # Verify counts
        assert result[0]['LESSON_COMPLETED'] == 3  # Third row
        assert result[1]['LESSON_COMPLETED'] == 1  # First row
        assert result[2]['LESSON_COMPLETED'] == 2  # Second row

    async def test_get_activity_details_same_date_different_types(self, mock_db):
        # Arrange
        user_id = 1

        mock_row1 = MagicMock()
        mock_row1.date = datetime(2024, 10, 1).date()
        mock_row1.activity_type = 'LESSON_COMPLETED'
        mock_row1.count = 3

        mock_row2 = MagicMock()
        mock_row2.date = datetime(2024, 10, 1).date()
        mock_row2.activity_type = 'CODE_EXECUTION'
        mock_row2.count = 7

        mock_row3 = MagicMock()
        mock_row3.date = datetime(2024, 10, 1).date()
        mock_row3.activity_type = 'QUIZ_ATTEMPT'
        mock_row3.count = 2

        mock_db.execute.return_value.all.return_value = [mock_row1, mock_row2, mock_row3]

        # Act
        result = await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        assert len(result) == 1
        day = result[0]
        assert day['date'] == '2024-10-01'
        assert day['LESSON_COMPLETED'] == 3
        assert day['CODE_EXECUTION'] == 7
        assert day['QUIZ_ATTEMPT'] == 2

    async def test_get_activity_details_query_parameters(self, mock_db):
        # Arrange
        user_id = 1
        mock_db.execute.return_value.all.return_value = []

        # Act
        await AnalyticsService.get_activity_details(user_id, mock_db)

        # Assert
        # Verify the query was called with correct parameters
        call_args = mock_db.execute.call_args[0][0]
        query_str = str(call_args)

        # Check that the query filters by user_id
        assert 'user_activity_logs.user_id' in query_str

        # Check that the query filters by timestamp (one year ago)
        assert 'user_activity_logs.timestamp >=' in query_str

        # Check grouping
        assert 'GROUP BY' in query_str

    async def test_track_activity_success(self, mock_db):
        # Arrange
        user_id = 1
        event_data = TrackEventRequest(
            activity_type='LESSON_COMPLETED',
            details={'lesson_slug': 'test-lesson', 'course_slug': 'test-course'}
        )

        # Act
        await AnalyticsService.track_activity(user_id, event_data, mock_db)

        # Assert
        # Verify that add was called with the correct UserActivityLog instance
        mock_db.add.assert_called_once()
        added_instance = mock_db.add.call_args[0][0]
        assert isinstance(added_instance, UserActivityLog)
        assert added_instance.user_id == user_id
        assert added_instance.activity_type == 'LESSON_COMPLETED'
        assert added_instance.details == {'lesson_slug': 'test-lesson', 'course_slug': 'test-course'}

        # Verify commit was called
        mock_db.commit.assert_called_once()

    async def test_track_activity_without_details(self, mock_db):
        # Arrange
        user_id = 2
        event_data = TrackEventRequest(
            activity_type='LOGIN',
            details=None
        )

        # Act
        await AnalyticsService.track_activity(user_id, event_data, mock_db)

        # Assert
        mock_db.add.assert_called_once()
        added_instance = mock_db.add.call_args[0][0]
        assert added_instance.user_id == user_id
        assert added_instance.activity_type == 'LOGIN'
        assert added_instance.details is None

        mock_db.commit.assert_called_once()

    async def test_track_activity_with_empty_details(self, mock_db):
        # Arrange
        user_id = 3
        event_data = TrackEventRequest(
            activity_type='CODE_EXECUTION',
            details={}
        )

        # Act
        await AnalyticsService.track_activity(user_id, event_data, mock_db)

        # Assert
        mock_db.add.assert_called_once()
        added_instance = mock_db.add.call_args[0][0]
        assert added_instance.user_id == user_id
        assert added_instance.activity_type == 'CODE_EXECUTION'
        assert added_instance.details == {}

        mock_db.commit.assert_called_once()
