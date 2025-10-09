import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.v1 import lessons as lessons_module
from src.api.v1.lessons import router as lessons_router
from src.dependencies import get_content_scanner, get_fs_service, get_ulf_parser
from src.core.security import get_current_admin
from src.core.config import settings
from pathlib import Path


@pytest.fixture
def mock_fs_service():
    """Mock FileSystemService."""
    service = MagicMock()
    service.read_file = AsyncMock()
    service.write_file = AsyncMock()
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
    service.clear_cache = MagicMock()
    return service


@pytest.fixture
def mock_get_current_admin():
    """Mock get_current_admin dependency."""
    return MagicMock()


@pytest.fixture
def test_app(mock_fs_service, mock_ulf_parser, mock_content_scanner, mock_get_current_admin):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(lessons_router, prefix="/api/lessons")

    # Override dependencies
    app.dependency_overrides[get_fs_service] = lambda: mock_fs_service
    app.dependency_overrides[get_ulf_parser] = lambda: mock_ulf_parser
    app.dependency_overrides[get_content_scanner] = lambda: mock_content_scanner
    app.dependency_overrides[get_current_admin] = lambda: mock_get_current_admin
    return app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app, raise_server_exceptions=False)


@pytest.fixture
def mock_find_lesson_file():
    with patch("src.api.v1.lessons._find_lesson_file") as mock:
        yield mock


class TestLessonsRawGet:
    def test_get_lesson_raw_success(self, client, mock_fs_service, mock_find_lesson_file):
        """Test successful raw lesson retrieval."""
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"
        mock_fs_service.read_file.return_value = '---\ntitle: Test Lesson\n---\n\nContent'

        response = client.get("/api/lessons/test-slug/raw")

        assert response.status_code == 200
        assert response.text == '---\ntitle: Test Lesson\n---\n\nContent'
        mock_fs_service.read_file.assert_called_once_with("courses/course/test-slug.lesson")

    def test_get_lesson_raw_not_found(self, client, mock_fs_service, mock_find_lesson_file):
        """Test raw lesson retrieval for non-existent file."""
        mock_find_lesson_file.side_effect = FileNotFoundError("missing")

        response = client.get("/api/lessons/missing/raw")

        assert response.status_code == 404
        assert "Lesson not found" in response.json()["detail"]

    def test_get_lesson_raw_security_error(self, client, mock_fs_service, mock_find_lesson_file):
        """Test raw lesson retrieval with security violation."""
        from src.core.errors import SecurityError
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"
        mock_fs_service.read_file.side_effect = SecurityError("Access denied")

        response = client.get("/api/lessons/test-slug/raw")

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


class TestLessonsRawPut:
    def test_put_lesson_raw_success(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner, mock_find_lesson_file):
        """Test successful raw lesson update."""
        content = '---\ntitle: Updated Lesson\n---\n\nNew content'
        mock_ulf_parser.parse.return_value = {"title": "Updated Lesson", "cells": []}
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        mock_ulf_parser.parse.assert_called_once_with(content)
        mock_fs_service.write_file.assert_called_once_with("courses/course/test-slug.lesson", content)
        mock_content_scanner.clear_cache.assert_called_once()

    def test_put_lesson_raw_parsing_error(self, client, mock_ulf_parser, mock_find_lesson_file):
        """Test raw lesson update with parsing error."""
        from src.core.errors import ParsingError
        mock_ulf_parser.parse.side_effect = ParsingError("Invalid YAML")
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"

        content = '---\ninvalid: yaml: [\n---\n\nContent'

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        assert "Invalid YAML" in response.json()["detail"]

    def test_put_lesson_raw_write_error(self, client, mock_fs_service, mock_ulf_parser, mock_content_scanner, mock_find_lesson_file):
        """Test raw lesson update with write error."""
        from src.core.errors import ContentFileNotFoundError
        mock_ulf_parser.parse.return_value = {"title": "Lesson", "cells": []}
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"
        mock_fs_service.write_file.side_effect = ContentFileNotFoundError("Cannot write")

        content = '---\ntitle: Lesson\n---\n\nContent'

        response = client.put(
            "/api/lessons/test-slug/raw",
            data=content,
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 404
        assert "Cannot write" in response.json()["detail"]
        mock_content_scanner.clear_cache.assert_not_called()

    def test_put_lesson_raw_empty_content(self, client, mock_ulf_parser, mock_find_lesson_file):
        """Test raw lesson update with empty content."""
        mock_ulf_parser.parse.return_value = {"title": "Empty", "cells": []}
        mock_find_lesson_file.return_value = Path(settings.CONTENT_ROOT) / "courses" / "course" / "test-slug.lesson"

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
