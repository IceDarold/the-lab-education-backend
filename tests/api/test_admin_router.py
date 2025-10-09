import pytest
from unittest.mock import AsyncMock, MagicMock
from src.schemas.content_node import ContentNode
from src.schemas.api import CreateCourseRequest, CreateModuleRequest, CreateLessonRequest
from tests.utils import assert_success_response, assert_error_response, assert_no_content


@pytest.mark.integration
class TestAdminContentTree:
    async def test_get_content_tree_success(self, async_client, mock_content_scanner):
        """Test successful content tree retrieval."""
        mock_content_scanner.build_content_tree.return_value = [
            ContentNode(type="course", name="ML Course", path="ml-course", children=[])
        ]

        response = await async_client.get("/api/admin/content-tree")
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        data = assert_success_response(response)

        assert len(data) == 1
        assert data[0]["type"] == "course"
        assert data[0]["name"] == "ML Course"
        mock_content_scanner.build_content_tree.assert_called_once()

    async def test_get_content_tree_service_error(self, async_client, mock_content_scanner):
        """Test content tree with service error."""
        mock_content_scanner.build_content_tree.side_effect = Exception("Service error")

        response = await async_client.get("/api/admin/content-tree")

        assert response.status_code == 500  # Or whatever the error handler returns


@pytest.mark.integration
class TestAdminConfigFile:
    async def test_get_config_file_success(self, async_client, mock_fs_service):
        """Test successful config file retrieval."""
        mock_fs_service.read_file.return_value = "title: ML Course\n"

        response = await async_client.get("/api/admin/config-file?path=_course.yml")

        assert_success_response(response)
        assert response.text == "title: ML Course\n"
        mock_fs_service.read_file.assert_called_once_with("_course.yml")

    async def test_get_config_file_not_found(self, async_client, mock_fs_service):
        """Test config file not found."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.read_file.side_effect = ContentFileNotFoundError("File not found")

        response = await async_client.get("/api/admin/config-file?path=missing.yml")

        assert_error_response(response, 404)
        assert "File not found" in response.json()["detail"]

    async def test_put_config_file_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful config file update."""
        content = "title: Updated Course\n"

        response = await async_client.put(
            "/api/admin/config-file?path=_course.yml",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        mock_fs_service.write_file.assert_called_once_with("_course.yml", content)
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_put_config_file_security_error(self, async_client, mock_fs_service, mock_content_scanner):
        """Test config file update with security error."""
        from src.core.errors import SecurityError
        mock_fs_service.write_file.side_effect = SecurityError("Access denied")

        response = await async_client.put(
            "/api/admin/config-file?path=../../../etc/passwd",
            data="malicious",
            headers={"Content-Type": "text/plain"}
        )

        assert_error_response(response, 403)
        assert "Access denied" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()


@pytest.mark.integration
class TestAdminCreateItem:
    async def test_create_course_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful course creation."""
        request_data = {"title": "New Course", "slug": "new-course"}

        response = await async_client.post("/api/admin/create/course", json=request_data)

        assert response.status_code == 201  # Keep as is for now, could use assert_created
        mock_fs_service.create_directory.assert_called_once_with("new-course")
        mock_fs_service.write_file.assert_called_once_with(
            "new-course/_course.yml", "title: New Course\n"
        )
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_create_module_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful module creation."""
        request_data = {"title": "New Module", "slug": "new-module", "parent_slug": "parent-course"}

        response = await async_client.post("/api/admin/create/module", json=request_data)

        assert response.status_code == 201  # Keep as is for now, could use assert_created
        mock_fs_service.create_directory.assert_called_once_with("parent-course/new-module")
        mock_fs_service.write_file.assert_called_once_with(
            "parent-course/new-module/_module.yml", "title: New Module\n"
        )
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_create_lesson_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful lesson creation."""
        request_data = {"title": "New Lesson", "slug": "new-lesson", "parent_slug": "parent-module"}

        response = await async_client.post("/api/admin/create/lesson", json=request_data)

        assert response.status_code == 201  # Keep as is for now, could use assert_created
        mock_fs_service.write_file.assert_called_once_with(
            "parent-module/new-lesson.lesson",
            '---\ntitle: New Lesson\n---\n\n# New Lesson\n\nContent goes here.\n'
        )
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_create_invalid_item_type(self, async_client):
        """Test creation with invalid item type."""
        request_data = {"title": "Invalid", "slug": "invalid"}

        response = await async_client.post("/api/admin/create/invalid", json=request_data)

        assert_error_response(response, 422)  # Unprocessable Entity for invalid path param

    async def test_create_course_validation_error(self, async_client, mock_fs_service):
        """Test course creation with invalid data."""
        request_data = {"title": "", "slug": "new-course"}  # Empty title

        response = await async_client.post("/api/admin/create/course", json=request_data)

        assert_error_response(response, 422)
        mock_fs_service.create_directory.assert_not_called()


@pytest.mark.integration
class TestAdminDeleteItem:
    async def test_delete_file_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful file deletion."""
        response = await async_client.delete("/api/admin/item?path=test.yml")

        assert_no_content(response)
        mock_fs_service.delete_file.assert_called_once_with("test.yml")
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_delete_directory_success(self, async_client, mock_fs_service, mock_content_scanner):
        """Test successful directory deletion."""
        # Mock path_exists to return True for directory
        mock_fs_service.path_exists = AsyncMock(return_value=True)
        mock_fs_service.scan_directory = AsyncMock(return_value=[])  # Empty dir

        response = await async_client.delete("/api/admin/item?path=test-dir")

        assert_no_content(response)
        mock_fs_service.delete_directory.assert_called_once_with("test-dir")
        mock_content_scanner.clear_cache.assert_called_once()

    async def test_delete_not_found(self, async_client, mock_fs_service, mock_content_scanner):
        """Test deletion of non-existent item."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.delete_file.side_effect = ContentFileNotFoundError("Not found")

        response = await async_client.delete("/api/admin/item?path=missing.yml")

        assert response.status_code == 404
        assert "Not found" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()