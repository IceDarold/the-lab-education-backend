import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from uuid import uuid4
from src.main import app  # Import the real app
from src.schemas.content_node import ContentNode
from src.dependencies import (
    get_fs_service,
    get_content_scanner,
    get_ulf_parser,
    require_current_user,
    require_current_admin,
    get_db,
)
from src.core.config import settings


async def _fake_db_session():
    yield AsyncMock()


@pytest.fixture
def mock_fs_service():
    """Mock FileSystemService for integration tests."""
    service = MagicMock()
    service.read_file = AsyncMock()
    service.write_file = AsyncMock()
    service.create_directory = AsyncMock()
    service.delete_file = AsyncMock()
    service.delete_directory = AsyncMock()
    service.path_exists = AsyncMock(return_value=True)
    service.scan_directory = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_content_scanner(mock_fs_service):
    """Mock ContentScannerService for integration tests."""
    service = MagicMock()
    service.build_content_tree = AsyncMock(return_value=[])
    service.clear_cache = MagicMock()
    return service


@pytest.fixture
def mock_ulf_parser():
    """Mock ULFParserService for integration tests."""
    service = MagicMock()
    service.parse = MagicMock(return_value={"title": "Test", "cells": []})
    return service


@pytest.fixture
def mock_get_current_admin():
    """Mock admin authentication."""
    admin = MagicMock()
    admin.role = "admin"
    admin.id = 1
    return admin


@pytest.fixture
def integration_app(mock_fs_service, mock_content_scanner, mock_ulf_parser, mock_get_current_admin):
    """Create integration test app with mocked services."""
    test_app = FastAPI()

    # Include the real routers
    from src.api.v1.admin import router as admin_router
    from src.api.v1.lessons import router as lessons_router
    test_app.include_router(admin_router, prefix="/api/admin")
    test_app.include_router(lessons_router, prefix="/api/lessons")

    # Override dependencies
    test_app.dependency_overrides[get_fs_service] = lambda: mock_fs_service
    test_app.dependency_overrides[get_content_scanner] = lambda: mock_content_scanner
    test_app.dependency_overrides[get_ulf_parser] = lambda: mock_ulf_parser
    test_app.dependency_overrides[require_current_admin] = lambda: mock_get_current_admin
    test_app.dependency_overrides[require_current_user] = lambda: mock_get_current_admin
    return test_app


@pytest.fixture
def client(integration_app):
    """Integration test client."""
    return TestClient(integration_app)


class TestAPIIntegration:
    def test_full_course_creation_workflow(self, client, mock_fs_service, mock_content_scanner):
        """Test complete workflow: create course, verify operations."""
        # Create course
        response = client.post("/api/admin/create/course", json={
            "title": "Integration Test Course",
            "slug": "integration-course"
        })

        assert response.status_code == 201

        # Verify service calls
        mock_fs_service.create_directory.assert_called_with("courses/integration-course")
        mock_fs_service.write_file.assert_called_with(
            "courses/integration-course/_course.yml",
            "title: Integration Test Course\n"
        )
        mock_content_scanner.clear_cache.assert_called()

    def test_content_tree_after_creation(self, client, mock_content_scanner):
        """Test content tree retrieval after creation."""
        mock_content_scanner.build_content_tree.return_value = [
            ContentNode(type="course", name="Test Course", path="test-course", children=[])
        ]

        response = client.get("/api/admin/content-tree")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Course"

    def test_lesson_update_workflow(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner):
        """Test lesson update with validation."""
        lesson_content = '---\ntitle: Updated Lesson\n---\n\nNew content'

        with patch("src.api.v1.lessons._find_lesson_file") as mock_find_lesson:
            mock_find_lesson.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-lesson.lesson"

            response = client.put(
                "/api/lessons/test-lesson/raw",
                data=lesson_content,
                headers={"Content-Type": "text/plain"}
            )

        assert response.status_code == 200

        # Verify parsing was called
        mock_ulf_parser.parse.assert_called_with(lesson_content)
        # Verify file was written
        mock_fs_service.write_file.assert_called_with("courses/course/test-lesson.lesson", lesson_content)
        # Verify cache was cleared
        mock_content_scanner.clear_cache.assert_called()

    def test_error_handling_integration(self, client, mock_fs_service):
        """Test error handling across the API."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.read_file.side_effect = ContentFileNotFoundError("File not found")

        # Test admin config file
        response = client.get("/api/admin/config-file?path=missing.yml")
        assert response.status_code == 404

        # Test lesson raw get
        response = client.get("/api/lessons/missing/raw")
        assert response.status_code == 404

    def test_security_integration(self, client, mock_fs_service):
        """Test security validation integration."""
        from src.core.errors import SecurityError
        mock_fs_service.read_file.side_effect = SecurityError("Access denied")

        response = client.get("/api/admin/config-file?path=../../../etc/passwd")
        assert response.status_code == 403

    def test_validation_integration(self, client):
        """Test request validation integration."""
        # Invalid course creation
        response = client.post("/api/admin/create/course", json={"title": ""})
        assert response.status_code == 422

        # Invalid lesson update
        response = client.put("/api/lessons/test/raw", json={"content": "invalid"})
        assert response.status_code == 422

    def test_crud_operations_integration(self, client, mock_fs_service, mock_content_scanner):
        """Test CRUD operations work together."""
        # Create
        client.post("/api/admin/create/course", json={
            "title": "CRUD Course",
            "slug": "crud-course"
        })

        # Read config
        mock_fs_service.read_file.return_value = "title: CRUD Course\n"
        response = client.get("/api/admin/config-file?path=crud-course/_course.yml")
        assert response.status_code == 200

        # Update config
        client.put(
            "/api/admin/config-file?path=crud-course/_course.yml",
            data="title: Updated CRUD Course\n",
            headers={"Content-Type": "text/plain"}
        )

        # Delete
        client.delete("/api/admin/item?path=crud-course/_course.yml")

        # Verify cache cleared multiple times
        # Verify cache cleared multiple times
        assert mock_content_scanner.clear_cache.call_count == 3

    def test_track_activity_success(self, client):
        """Test successful activity tracking returns 202."""
        # Mock authenticated user
        from unittest.mock import patch
        from src.routers.analytics_router import router as analytics_router
        client.app.include_router(analytics_router, prefix="/api")

        mock_user = MagicMock()
        mock_user.user_id = uuid4()

        client.app.dependency_overrides[require_current_user] = lambda: mock_user
        client.app.dependency_overrides[get_db] = _fake_db_session

        with patch("src.services.analytics_service.AnalyticsService.track_activity") as mock_track:
            mock_track.return_value = None
            response = client.post("/api/activity-log", json={
                "activity_type": "LESSON_COMPLETED",
                "details": {"lesson_slug": "test-lesson", "course_slug": "test-course"}
            })

        client.app.dependency_overrides.pop(require_current_user, None)
        client.app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 202
                # Verify background task would be called (can't easily test background tasks in TestClient)

    def test_track_activity_unauthenticated(self, client):
        """Test activity tracking without authentication returns 401."""
        # Include analytics router
        from src.routers.analytics_router import router as analytics_router
        client.app.include_router(analytics_router, prefix="/api")

        original_user_override = client.app.dependency_overrides.pop(require_current_user, None)
        original_db_override = client.app.dependency_overrides.pop(get_db, None)

        response = client.post("/api/activity-log", json={
            "activity_type": "LOGIN"
        })

        assert response.status_code == 401

        if original_user_override is not None:
            client.app.dependency_overrides[require_current_user] = original_user_override
        if original_db_override is not None:
            client.app.dependency_overrides[get_db] = original_db_override

    def test_track_activity_invalid_data(self, client):
        """Test activity tracking with invalid data returns 422."""
        # Mock authenticated user
        from unittest.mock import patch
        from src.routers.analytics_router import router as analytics_router
        client.app.include_router(analytics_router, prefix="/api")

        mock_user = MagicMock()
        mock_user.user_id = uuid4()

        client.app.dependency_overrides[require_current_user] = lambda: mock_user
        client.app.dependency_overrides[get_db] = _fake_db_session

        response = client.post("/api/activity-log", json={
            "activity_type": "INVALID_TYPE",
            "details": {"key": "value"}
        })

        client.app.dependency_overrides.pop(require_current_user, None)
        client.app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 422
