import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from src.dependencies import get_current_user, get_db
from src.routers.analytics_router import router as analytics_router
from src.schemas.analytics import TrackEventRequest


@pytest.fixture
def mock_analytics_service():
    """Mock AnalyticsService."""
    service = SimpleNamespace(
        track_activity=AsyncMock(),
        get_activity_details=AsyncMock(),
    )
    return service


@pytest.fixture
def mock_get_current_user():
    """Mock get_current_user dependency."""
    user = MagicMock()
    user.id = "test-user-id"
    return user


@pytest.fixture
def mock_get_db():
    """Mock get_db dependency."""
    return MagicMock()


@pytest.fixture
def test_app(mock_analytics_service, mock_get_current_user, mock_get_db):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(analytics_router)

    async def override_get_db():
        yield mock_get_db

    async def override_get_current_user_dep():
        return mock_get_current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user_dep

    with patch("src.services.analytics_service.AnalyticsService.track_activity", new=mock_analytics_service.track_activity), \
         patch("src.services.analytics_service.AnalyticsService.get_activity_details", new=mock_analytics_service.get_activity_details):
        yield app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app, raise_server_exceptions=False)


class TestAnalyticsRouter:
    def test_track_user_activity_success(self, client, mock_analytics_service, mock_get_current_user, mock_get_db):
        """Test successful activity tracking."""
        request_data = {
            "activity_type": "LESSON_COMPLETED",
            "details": {"lesson_slug": "test-lesson", "course_slug": "test-course"}
        }

        response = client.post("/activity-log", json=request_data)

        assert response.status_code == 202
        # Background tasks return JSON null
        assert response.json() is None
        mock_analytics_service.track_activity.assert_called_once_with(
            user_id=mock_get_current_user.id,
            event_data=TrackEventRequest(**request_data),
            db=mock_get_db
        )

    def test_track_user_activity_minimal_data(self, client, mock_analytics_service, mock_get_current_user, mock_get_db):
        """Test activity tracking with minimal data (no details)."""
        request_data = {
            "activity_type": "LOGIN"
        }

        response = client.post("/activity-log", json=request_data)

        assert response.status_code == 202
        mock_analytics_service.track_activity.assert_called_once_with(
            user_id=mock_get_current_user.id,
            event_data=TrackEventRequest(activity_type="LOGIN", details=None),
            db=mock_get_db
        )

    def test_track_user_activity_invalid_data(self, client):
        """Test activity tracking with invalid data."""
        request_data = {
            "invalid_field": "value"
        }

        response = client.post("/activity-log", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_get_user_activity_details_success(self, client, mock_analytics_service, mock_get_current_user, mock_get_db):
        """Test successful retrieval of activity details."""
        mock_activities = [
            {"date": "2023-10-01", "LOGIN": 2, "LESSON_COMPLETED": 1},
            {"date": "2023-10-02", "QUIZ_ATTEMPT": 3}
        ]
        mock_analytics_service.get_activity_details.return_value = mock_activities

        response = client.get("/activity-log")

        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert len(data["activities"]) == 2
        assert data["activities"][0]["date"] == "2023-10-01"
        assert data["activities"][0]["LOGIN"] == 2
        assert data["activities"][0]["LESSON_COMPLETED"] == 1
        mock_analytics_service.get_activity_details.assert_called_once_with(
            mock_get_current_user.id, mock_get_db
        )

    def test_get_user_activity_details_empty(self, client, mock_analytics_service, mock_get_current_user, mock_get_db):
        """Test retrieval of activity details when no activities exist."""
        mock_analytics_service.get_activity_details.return_value = []

        response = client.get("/activity-log")

        assert response.status_code == 200
        data = response.json()
        assert data["activities"] == []
        mock_analytics_service.get_activity_details.assert_called_once_with(
            mock_get_current_user.id, mock_get_db
        )

    def test_get_user_activity_details_service_error(self, client, mock_analytics_service):
        """Test activity details retrieval with service error."""
        mock_analytics_service.get_activity_details.side_effect = Exception("Database error")

        response = client.get("/activity-log")

        assert response.status_code == 500
