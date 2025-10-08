import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from src.api.v1.lessons import router as lessons_router


@pytest.fixture
def mock_fs_service():
    """Mock FileSystemService."""
    service = MagicMock()
    service.readFile = AsyncMock()
    service.writeFile = AsyncMock()
    return service


@pytest.fixture
def mock_ulf_parser():
    """Mock ULFParserService."""
    service = MagicMock()
    service.parse = MagicMock()
    return service


@pytest.fixture
def mock_content_scanner():
    """Mock ContentScannerService."""
    service = MagicMock()
    service.clear_cache = AsyncMock()
    return service


@pytest.fixture
def mock_get_current_admin():
    """Mock get_current_admin dependency."""
    return MagicMock()


@pytest.fixture
def test_app(mock_fs_service, mock_ulf_parser, mock_content_scanner, mock_get_current_admin):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(lessons_router)

    # Override dependencies
    app.dependency_overrides = {
        "src.dependencies.get_fs_service": lambda: mock_fs_service,
        "src.dependencies.get_ulf_parser": lambda: mock_ulf_parser,
        "src.dependencies.get_content_scanner": lambda: mock_content_scanner,
        "src.core.security.get_current_admin": lambda: mock_get_current_admin,
    }
    return app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app)


class TestLessonsRawGet:
    def test_get_lesson_raw_success(self, client, mock_fs_service):
        """Test successful raw lesson retrieval."""
        mock_fs_service.readFile.return_value = '---\ntitle: Test Lesson\n---\n\nContent'

        response = client.get("/api/lessons/test-slug/raw")

        assert response.status_code == 200
        assert response.text == '---\ntitle: Test Lesson\n---\n\nContent'
        mock_fs_service.readFile.assert_called_once_with("test-slug.lesson")

    def test_get_lesson_raw_not_found(self, client, mock_fs_service):
        """Test raw lesson retrieval for non-existent file."""
        from src.core.errors import FileNotFoundError
        mock_fs_service.readFile.side_effect = FileNotFoundError("Lesson not found")

        response = client.get("/api/lessons/missing/raw")

        assert response.status_code == 404
        assert "Lesson not found" in response.json()["detail"]

    def test_get_lesson_raw_security_error(self, client, mock_fs_service):
        """Test raw lesson retrieval with security violation."""
        from src.core.errors import SecurityError
        mock_fs_service.readFile.side_effect = SecurityError("Access denied")

        response = client.get("/api/lessons/../../../etc/passwd/raw")

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


class TestLessonsRawPut:
    def test_put_lesson_raw_success(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner):
        """Test successful raw lesson update."""
        content = '---\ntitle: Updated Lesson\n---\n\nNew content'
        mock_ulf_parser.parse.return_value = {"title": "Updated Lesson", "cells": []}

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        mock_ulf_parser.parse.assert_called_once_with(content)
        mock_fs_service.writeFile.assert_called_once_with("test-slug.lesson", content)
        mock_content_scanner.clear_cache.assert_called_once()

    def test_put_lesson_raw_parsing_error(self, client, mock_ulf_parser):
        """Test raw lesson update with parsing error."""
        from src.core.errors import ParsingError
        mock_ulf_parser.parse.side_effect = ParsingError("Invalid YAML")

        content = '---\ninvalid: yaml: [\n---\n\nContent'

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        assert "Invalid YAML" in response.json()["detail"]

    def test_put_lesson_raw_write_error(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner):
        """Test raw lesson update with write error."""
        from src.core.errors import FileNotFoundError
        mock_ulf_parser.parse.return_value = {"title": "Lesson", "cells": []}
        mock_fs_service.writeFile.side_effect = FileNotFoundError("Cannot write")

        content = '---\ntitle: Lesson\n---\n\nContent'

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 404
        assert "Cannot write" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()

    def test_put_lesson_raw_empty_content(self, client, mock_ulf_parser):
        """Test raw lesson update with empty content."""
        mock_ulf_parser.parse.return_value = {"title": "Empty", "cells": []}

        response = client.put(
            "/api/lessons/test-slug/raw",
            data="",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        mock_ulf_parser.parse.assert_called_once_with("")

    def test_put_lesson_raw_invalid_content_type(self, client):
        """Test raw lesson update with invalid content type."""
        response = client.put(
            "/api/lessons/test-slug/raw",
            json={"content": "test"}  # Wrong content type
        )

        assert response.status_code == 422  # FastAPI validation error