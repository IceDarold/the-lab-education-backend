import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from src.routers.admin.users_router import router as users_router
from src.schemas import UsersListResponse, UserResponse, UserFilter
from src.models.user import User
from src.models.enrollment import Enrollment
from datetime import datetime


@pytest.fixture
def mock_user_service():
    """Mock UserService."""
    service = MagicMock()
    service.list_users = AsyncMock()
    return service


@pytest.fixture
def mock_progress_service():
    """Mock ProgressService."""
    service = MagicMock()
    service.get_user_progress_for_course = AsyncMock()
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock AnalyticsService."""
    service = MagicMock()
    service.get_activity_details = AsyncMock()
    return service


@pytest.fixture
def mock_content_scanner():
    """Mock ContentScannerService."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_get_current_admin():
    """Mock get_current_admin dependency."""
    admin = MagicMock()
    admin.id = 1
    admin.role = "admin"
    return admin


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def test_app(mock_user_service, mock_progress_service, mock_analytics_service, mock_content_scanner, mock_get_current_admin, mock_db):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(users_router, prefix="/api/admin/users")

    # Override dependencies
    app.dependency_overrides = {
        "src.dependencies.get_db": lambda: mock_db,
        "src.core.security.get_current_admin": lambda: mock_get_current_admin,
        "src.services.user_service.UserService": lambda: mock_user_service,
        "src.services.progress_service.ProgressService": lambda: mock_progress_service,
        "src.services.analytics_service.AnalyticsService": lambda: mock_analytics_service,
        "src.dependencies.get_content_scanner": lambda: mock_content_scanner,
    }
    return app


@pytest.fixture
async def client(test_app):
    """Async test client."""
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac


class TestListUsers:
    def test_list_users_success_no_filters(self, client, mock_user_service, mock_db):
        """Test successful user listing without filters."""
        # Mock users
        mock_users = [
            User(id=1, full_name="John Doe", email="john@example.com", role="STUDENT", status="ACTIVE", registration_date=datetime.now()),
            User(id=2, full_name="Jane Smith", email="jane@example.com", role="ADMIN", status="ACTIVE", registration_date=datetime.now()),
        ]
        mock_user_service.list_users.return_value = mock_users

        # Mock count query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute.return_value = mock_result

        response = client.get("/api/admin/users/")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2
        assert data["total_items"] == 2
        assert data["total_pages"] == 1
        assert data["current_page"] == 1
        assert data["page_size"] == 10
        mock_user_service.list_users.assert_called_once_with(db=mock_db, filters=UserFilter())

    def test_list_users_success_with_filters(self, client, mock_user_service, mock_db):
        """Test successful user listing with filters."""
        mock_users = [
            User(id=1, full_name="John Doe", email="john@example.com", role="STUDENT", status="ACTIVE", registration_date=datetime.now()),
        ]
        mock_user_service.list_users.return_value = mock_users

        # Mock count query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute.return_value = mock_result

        response = client.get("/api/admin/users/?search=john&role=STUDENT&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        assert data["total_items"] == 1
        assert data["page_size"] == 5
        filters = UserFilter(search="john", role="STUDENT", limit=5)
        mock_user_service.list_users.assert_called_once_with(db=mock_db, filters=filters)

    def test_list_users_success_pagination(self, client, mock_user_service, mock_db):
        """Test user listing with pagination."""
        mock_users = [
            User(id=2, full_name="Jane Smith", email="jane@example.com", role="ADMIN", status="ACTIVE", registration_date=datetime.now()),
        ]
        mock_user_service.list_users.return_value = mock_users

        mock_result = MagicMock()
        mock_result.scalar.return_value = 12
        mock_db.execute.return_value = mock_result

        response = client.get("/api/admin/users/?skip=10&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 12
        assert data["total_pages"] == 3  # ceil(12/5)
        assert data["current_page"] == 3  # 10//5 + 1
        assert data["page_size"] == 5

    def test_list_users_database_error(self, client, mock_user_service, mock_db):
        """Test list_users with database error."""
        mock_user_service.list_users.side_effect = Exception("Database error")

        response = client.get("/api/admin/users/")

        assert response.status_code == 500


class TestGetUserDetails:
    def test_get_user_details_success(self, client, mock_db, mock_progress_service, mock_analytics_service):
        """Test successful user details retrieval."""
        # Mock user
        mock_user = User(id=1, full_name="John Doe", email="john@example.com", role="STUDENT", status="ACTIVE", registration_date=datetime.now())
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        # Mock enrollments
        mock_enrollment_result = MagicMock()
        mock_enrollment_result.__iter__ = lambda self: iter([MagicMock(course_slug="course1"), MagicMock(course_slug="course2")])
        mock_db.execute.return_value = mock_enrollment_result

        # Mock progress
        mock_progress_service.get_user_progress_for_course.return_value = {"completed": 5, "total": 10}

        # Mock activity
        mock_analytics_service.get_activity_details.return_value = [{"date": "2023-10-01", "LOGIN": 2}]

        response = client.get("/api/admin/users/1/details")

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "activity" in data
        assert "progress" in data
        assert data["progress"]["course1"] == {"completed": 5, "total": 10}
        assert data["progress"]["course2"] == {"completed": 5, "total": 10}
        mock_analytics_service.get_activity_details.assert_called_once_with(user_id=1, db=mock_db)

    def test_get_user_details_user_not_found(self, client, mock_db):
        """Test user details when user not found."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        response = client.get("/api/admin/users/999/details")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_details_progress_service_error(self, client, mock_db, mock_progress_service, mock_analytics_service):
        """Test user details with progress service error."""
        mock_user = User(id=1, full_name="John Doe", email="john@example.com", role="STUDENT", status="ACTIVE", registration_date=datetime.now())
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        mock_enrollment_result = MagicMock()
        mock_enrollment_result.__iter__ = lambda self: iter([MagicMock(course_slug="course1")])
        mock_db.execute.return_value = mock_enrollment_result

        mock_progress_service.get_user_progress_for_course.side_effect = Exception("Progress error")

        response = client.get("/api/admin/users/1/details")

        assert response.status_code == 500

    def test_get_user_details_analytics_service_error(self, client, mock_db, mock_progress_service, mock_analytics_service):
        """Test user details with analytics service error."""
        mock_user = User(id=1, full_name="John Doe", email="john@example.com", role="STUDENT", status="ACTIVE", registration_date=datetime.now())
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        mock_enrollment_result = MagicMock()
        mock_enrollment_result.__iter__ = lambda self: iter([])
        mock_db.execute.return_value = mock_enrollment_result

        mock_analytics_service.get_activity_details.side_effect = Exception("Analytics error")

        response = client.get("/api/admin/users/1/details")

        assert response.status_code == 500