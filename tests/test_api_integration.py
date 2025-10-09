import pytest
from unittest.mock import AsyncMock, MagicMock
from src.schemas.content_node import ContentNode
from tests.utils import assert_success_response, assert_error_response, assert_created


@pytest.mark.integration
class TestAPIIntegration:
    def test_full_course_creation_workflow(self, client, mock_fs_service, mock_content_scanner):
        """Test complete workflow: create course, verify operations."""
        # Create course
        response = client.post("/api/admin/create/course", json={
            "title": "Integration Test Course",
            "slug": "integration-course"
        })

        assert_created(response)

        # Verify service calls
        mock_fs_service.createDirectory.assert_called_with("integration-course")
        mock_fs_service.writeFile.assert_called_with(
            "integration-course/_course.yml",
            "title: Integration Test Course\n"
        )
        mock_content_scanner.clear_cache.assert_called()

    def test_content_tree_after_creation(self, client, mock_content_scanner):
        """Test content tree retrieval after creation."""
        mock_content_scanner.build_content_tree.return_value = [
            ContentNode(type="course", name="Test Course", path="test-course", children=[])
        ]

        response = client.get("/api/admin/content-tree")
        data = assert_success_response(response)

        assert len(data) == 1
        assert data[0]["name"] == "Test Course"

    def test_lesson_update_workflow(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner):
        """Test lesson update with validation."""
        lesson_content = '---\ntitle: Updated Lesson\n---\n\nNew content'

        response = client.put(
            "/api/lessons/test-lesson/raw",
            data=lesson_content,
            headers={"Content-Type": "text/plain"}
        )

        assert_success_response(response)

        # Verify parsing was called
        mock_ulf_parser.parse.assert_called_with(lesson_content)
        # Verify file was written
        mock_fs_service.writeFile.assert_called_with("test-lesson.lesson", lesson_content)
        # Verify cache was cleared
        mock_content_scanner.clear_cache.assert_called()

    def test_error_handling_integration(self, client, mock_fs_service):
        """Test error handling across the API."""
        from src.core.errors import ContentFileNotFoundError
        mock_fs_service.readFile.side_effect = ContentFileNotFoundError("File not found")

        # Test admin config file
        response = client.get("/api/admin/config-file?path=missing.yml")
        assert_error_response(response, 404)

        # Test lesson raw get
        response = client.get("/api/lessons/missing/raw")
        assert_error_response(response, 404)

    def test_security_integration(self, client, mock_fs_service):
        """Test security validation integration."""
        from src.core.errors import SecurityError
        mock_fs_service.readFile.side_effect = SecurityError("Access denied")

        response = client.get("/api/admin/config-file?path=../../../etc/passwd")
        assert_error_response(response, 403)

    def test_validation_integration(self, client):
        """Test request validation integration."""
        # Invalid course creation
        response = client.post("/api/admin/create/course", json={"title": ""})
        assert_error_response(response, 422)

        # Invalid lesson update
        response = client.put("/api/lessons/test/raw", json={"content": "invalid"})
        assert_error_response(response, 422)

    def test_crud_operations_integration(self, client, mock_fs_service, mock_content_scanner):
        """Test CRUD operations work together."""
        # Create
        client.post("/api/admin/create/course", json={
            "title": "CRUD Course",
            "slug": "crud-course"
        })

        # Read config
        mock_fs_service.readFile.return_value = "title: CRUD Course\n"
        response = client.get("/api/admin/config-file?path=crud-course/_course.yml")
        assert_success_response(response)

        # Update config
        client.put(
            "/api/admin/config-file?path=crud-course/_course.yml",
            data="title: Updated CRUD Course\n",
            headers={"Content-Type": "text/plain"}
        )

        # Delete
        client.delete("/api/admin/item?path=crud-course/_course.yml")

        # Verify cache cleared multiple times
        assert mock_content_scanner.clear_cache.call_count == 3

    def test_track_activity_success(self, client):
        """Test successful activity tracking returns 202."""
        # Mock authenticated user
        from unittest.mock import patch
        with patch('src.dependencies.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user

            # Mock database session
            with patch('src.dependencies.get_db') as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db

                # Include analytics router in test app
                from src.routers.analytics_router import router as analytics_router
                client.app.include_router(analytics_router, prefix="/api")

                # Test successful tracking
                response = client.post("/api/activity-log", json={
                    "activity_type": "LESSON_COMPLETED",
                    "details": {"lesson_slug": "test-lesson", "course_slug": "test-course"}
                })

                assert response.status_code == 202
                # Verify background task would be called (can't easily test background tasks in TestClient)

    def test_track_activity_unauthenticated(self, client):
        """Test activity tracking without authentication returns 401."""
        # Include analytics router
        from src.routers.analytics_router import router as analytics_router
        client.app.include_router(analytics_router, prefix="/api")

        response = client.post("/api/activity-log", json={
            "activity_type": "LOGIN"
        })

        assert_error_response(response, 401)

    def test_track_activity_invalid_data(self, client):
        """Test activity tracking with invalid data returns 422."""
        # Mock authenticated user
        from unittest.mock import patch
        with patch('src.dependencies.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user

            # Include analytics router
            from src.routers.analytics_router import router as analytics_router
            client.app.include_router(analytics_router, prefix="/api")

            # Test invalid activity_type
            response = client.post("/api/activity-log", json={
                "activity_type": "INVALID_TYPE",
                "details": {"key": "value"}
            })

            assert_error_response(response, 422)