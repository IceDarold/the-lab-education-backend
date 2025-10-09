import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.api.v1.admin import router as admin_router
from src.dependencies import get_content_scanner, get_fs_service, require_current_admin
from src.schemas.content_node import ContentNode
from src.schemas.user import User


@pytest.fixture
def mock_fs_service():
    """Mock FileSystemService."""
    service = MagicMock()
    service.read_file = AsyncMock()
    service.write_file = AsyncMock()
    service.create_directory = AsyncMock()
    service.delete_file = AsyncMock()
    service.delete_directory = AsyncMock()
    service.scan_directory = AsyncMock()
    service.path_exists = AsyncMock(return_value=False)
    return service


@pytest.fixture
def mock_content_scanner():
    """Mock ContentScannerService."""
    service = MagicMock()
    service.build_content_tree = AsyncMock()
    service.clear_cache = MagicMock()
    return service


@pytest.fixture
def mock_get_current_admin():
    """Mock get_current_admin dependency."""
    return User.model_construct(
        user_id=uuid4(),
        full_name="Admin User",
        email="admin@test.com",
        role="admin"
    )


@pytest.fixture
def test_app(mock_fs_service, mock_content_scanner, mock_get_current_admin):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()

    # Override dependencies before including router
    async def mock_get_current_admin_dep():
        return mock_get_current_admin

    async def override_fs_service():
        return mock_fs_service

    async def override_content_scanner():
        return mock_content_scanner

    app.dependency_overrides[get_fs_service] = override_fs_service
    app.dependency_overrides[get_content_scanner] = override_content_scanner
    app.dependency_overrides[require_current_admin] = mock_get_current_admin_dep

    app.include_router(admin_router, prefix="/api/admin")
    return app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app)


class TestAdminContentTree:
    def test_get_content_tree_success(self, client, mock_content_scanner):
        """Test successful content tree retrieval."""
        mock_content_scanner.build_content_tree.return_value = [
            ContentNode(type="course", name="ML Course", path="ml-course", children=[])
        ]

        response = client.get("/api/admin/content-tree")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "course"
        assert data[0]["name"] == "ML Course"
        mock_content_scanner.build_content_tree.assert_called_once()

    def test_get_content_tree_service_error(self, client, mock_content_scanner):
        """Test content tree with service error."""
        mock_content_scanner.build_content_tree.side_effect = Exception("Service error")

        response = client.get("/api/admin/content-tree")

        assert response.status_code == 500  # Or whatever the error handler returns


class TestAdminConfigFile:
    def test_get_config_file_success(self, client, mock_fs_service):
        """Test successful config file retrieval."""
        mock_fs_service.read_file.return_value = "title: ML Course\n"

        response = client.get("/api/admin/config-file?path=_course.yml")

        assert response.status_code == 200
        assert response.text == "title: ML Course\n"
        mock_fs_service.read_file.assert_called_once_with("_course.yml")

    def test_get_config_file_not_found(self, client, mock_fs_service):
        """Test config file not found."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.read_file.side_effect = ContentFileNotFoundError("File not found")

        response = client.get("/api/admin/config-file?path=missing.yml")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_put_config_file_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful config file update."""
        content = "title: Updated Course\n"

        response = client.put(
            "/api/admin/config-file?path=_course.yml",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        mock_fs_service.write_file.assert_called_once_with("_course.yml", content)
        mock_content_scanner.clear_cache.assert_called_once()

    def test_put_config_file_security_error(self, client, mock_fs_service, mock_content_scanner):
        """Test config file update with security error."""
        from src.core.errors import SecurityError
        mock_fs_service.write_file.side_effect = SecurityError("Access denied")

        response = client.put(
            "/api/admin/config-file?path=../../../etc/passwd",
            data="malicious",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()


class TestAdminCreateItem:
    def test_create_course_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful course creation."""
        request_data = {"title": "New Course", "slug": "new-course"}

        response = client.post("/api/admin/create/course", json=request_data)

        assert response.status_code == 201
        mock_fs_service.create_directory.assert_called_once_with("courses/new-course")
        mock_fs_service.write_file.assert_called_once_with(
            "courses/new-course/_course.yml", "title: New Course\n"
        )
        mock_content_scanner.clear_cache.assert_called_once()

    def test_create_module_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful module creation."""
        request_data = {"title": "New Module", "slug": "new-module", "parent_slug": "parent-course"}

        response = client.post("/api/admin/create/module", json=request_data)

        assert response.status_code == 201
        mock_fs_service.create_directory.assert_called_once_with("courses/parent-course/new-module")
        mock_fs_service.write_file.assert_called_once_with(
            "courses/parent-course/new-module/_module.yml", "title: New Module\n"
        )
        mock_content_scanner.clear_cache.assert_called_once()

    def test_create_lesson_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful lesson creation."""
        request_data = {"title": "New Lesson", "slug": "new-lesson", "parent_slug": "parent-module"}
        mock_content_scanner.build_content_tree.return_value = [
            ContentNode(
                type="course",
                name="parent-course",
                path="courses/parent-course",
                config_path="courses/parent-course/_course.yml",
                children=[
                    ContentNode(
                        type="module",
                        name="parent-module",
                        path="courses/parent-course/parent-module",
                        config_path="courses/parent-course/parent-module/_module.yml",
                        children=[],
                    )
                ],
            )
        ]

        response = client.post("/api/admin/create/lesson", json=request_data)

        assert response.status_code == 201
        mock_fs_service.write_file.assert_called_once()
        args, _ = mock_fs_service.write_file.call_args
        assert args[0].endswith("parent-module/new-lesson.lesson")
        mock_content_scanner.clear_cache.assert_called_once()

    def test_create_invalid_item_type(self, client):
        """Test creation with invalid item type."""
        request_data = {"title": "Invalid", "slug": "invalid"}

        response = client.post("/api/admin/create/invalid", json=request_data)

        assert response.status_code == 422  # Unprocessable Entity for invalid path param

    def test_create_course_validation_error(self, client, mock_fs_service):
        """Test course creation with invalid data."""
        request_data = {"title": "", "slug": "new-course"}  # Empty title

        response = client.post("/api/admin/create/course", json=request_data)

        assert response.status_code == 422
        mock_fs_service.create_directory.assert_not_called()


class TestAdminDeleteItem:
    def test_delete_file_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful file deletion."""
        mock_fs_service.path_exists.return_value = True
        response = client.delete("/api/admin/item?path=test.yml")

        assert response.status_code == 204
        mock_fs_service.delete_file.assert_called_once_with("test.yml")
        mock_content_scanner.clear_cache.assert_called_once()

    def test_delete_directory_success(self, client, mock_fs_service, mock_content_scanner):
        """Test successful directory deletion."""
        # Mock pathExists to return True for directory
        mock_fs_service.path_exists.return_value = True
        mock_fs_service.delete_directory = AsyncMock()

        response = client.delete("/api/admin/item?path=test-dir")

        assert response.status_code == 204
        mock_fs_service.delete_directory.assert_called_once_with("test-dir")
        mock_content_scanner.clear_cache.assert_called_once()

    def test_delete_not_found(self, client, mock_fs_service, mock_content_scanner):
        """Test deletion of non-existent item."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.path_exists.return_value = True
        mock_fs_service.delete_file.side_effect = ContentFileNotFoundError("Not found")

        response = client.delete("/api/admin/item?path=missing.yml")

        assert response.status_code == 404
        assert "Not found" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()
