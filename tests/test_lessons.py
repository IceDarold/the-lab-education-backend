import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.core.security import get_current_user
from src.main import app
from src.schemas.user import User


def _write_lesson_file(base_dir: Path, course: str, slug: str) -> Path:
    lesson_dir = base_dir / "courses" / course
    lesson_dir.mkdir(parents=True, exist_ok=True)
    file_path = lesson_dir / f"{slug}.lesson"
    file_path.write_text(
        """
---
title: Sample Lesson
slug: sample-lesson
course_slug: sample-course
lesson_id: "11111111-1111-1111-1111-111111111111"
duration: 15m
---
type: markdown
order: 1
---
# Welcome to the lesson

---
type: code
language: python
---
print("Hello")
""".strip()
    )
    return file_path


def _override_user():
    return User(
        user_id=UUID("22222222-2222-2222-2222-222222222222"),
        full_name="Tester",
        email="tester@example.com",
    )


@pytest.mark.asyncio
async def test_get_lesson_content_success(tmp_path, monkeypatch):
    content_root = tmp_path / "content"
    _write_lesson_file(content_root, "sample-course", "sample-lesson")

    monkeypatch.setattr(settings, "CONTENT_ROOT", str(content_root))
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/lessons/sample-lesson",
            headers={"Authorization": "Bearer token"},
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "sample-lesson"
    assert payload["title"] == "Sample Lesson"
    assert payload["course_slug"] == "sample-course"
    assert payload["lesson_id"] == "11111111-1111-1111-1111-111111111111"
    assert len(payload["cells"]) == 2
    assert payload["cells"][0]["cell_type"] == "markdown"
    assert "Welcome" in payload["cells"][0]["content"]


@pytest.mark.asyncio
async def test_get_lesson_content_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "CONTENT_ROOT", str(tmp_path / "content"))
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/lessons/missing-lesson",
            headers={"Authorization": "Bearer token"},
        )

    app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_lesson_parse_error(tmp_path, monkeypatch):
    content_root = tmp_path / "content"
    lesson_dir = content_root / "courses" / "sample-course"
    lesson_dir.mkdir(parents=True, exist_ok=True)
    (lesson_dir / "broken.lesson").write_text("no-front-matter here")

    monkeypatch.setattr(settings, "CONTENT_ROOT", str(content_root))
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/lessons/broken",
            headers={"Authorization": "Bearer token"},
        )

    app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_complete_lesson_success():
    app.dependency_overrides[get_current_user] = _override_user

    with patch('src.db.session.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase

        # Mock upsert
        mock_upsert_result = MagicMock()
        mock_upsert_result.execute = MagicMock(return_value=AsyncMock(return_value={"data": None}))
        mock_supabase.table.return_value.upsert.return_value = mock_upsert_result

        # Mock rpc
        mock_rpc_result = AsyncMock(return_value={"data": {"new_course_progress_percent": 75}})
        mock_supabase.rpc.return_value = mock_rpc_result

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lessons/sample-course/sample-lesson/complete",
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["new_course_progress_percent"] == 75


@pytest.mark.asyncio
async def test_complete_lesson_invalid_format_no_slash():
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/lessons/invalidlessonid/complete",
            headers={"Authorization": "Bearer token"},
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    payload = response.json()
    assert "Invalid lesson_id format" in payload["detail"]


@pytest.mark.asyncio
async def test_complete_lesson_invalid_format_empty_parts():
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/lessons//sample-lesson/complete",
            headers={"Authorization": "Bearer token"},
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    payload = response.json()
    assert "Invalid lesson_id format" in payload["detail"]


@pytest.mark.asyncio
async def test_complete_lesson_upsert_failure():
    app.dependency_overrides[get_current_user] = _override_user

    with patch('src.db.session.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase

        # Mock upsert to raise exception
        mock_upsert_result = MagicMock()
        mock_upsert_result.execute = MagicMock(return_value=AsyncMock(side_effect=Exception("Upsert failed")))
        mock_supabase.table.return_value.upsert.return_value = mock_upsert_result

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lessons/sample-course/sample-lesson/complete",
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 500  # Assuming internal server error for db failures


@pytest.mark.asyncio
async def test_complete_lesson_rpc_failure():
    app.dependency_overrides[get_current_user] = _override_user

    with patch('src.db.session.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase

        # Mock upsert success
        mock_upsert_result = MagicMock()
        mock_upsert_result.execute = MagicMock(return_value=AsyncMock(return_value={"data": None}))
        mock_supabase.table.return_value.upsert.return_value = mock_upsert_result

        # Mock rpc to raise exception
        mock_supabase.rpc.return_value = AsyncMock(side_effect=Exception("RPC failed"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lessons/sample-course/sample-lesson/complete",
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_complete_lesson_missing_progress_data():
    app.dependency_overrides[get_current_user] = _override_user

    with patch('src.db.session.get_supabase_client') as mock_get_client:
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase

        # Mock upsert
        mock_upsert_result = MagicMock()
        mock_upsert_result.execute = MagicMock(return_value=AsyncMock(return_value={"data": None}))
        mock_supabase.table.return_value.upsert.return_value = mock_upsert_result

        # Mock rpc with missing progress data
        mock_rpc_result = AsyncMock(return_value={"data": {}})
        mock_supabase.rpc.return_value = mock_rpc_result

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/lessons/sample-course/sample-lesson/complete",
                headers={"Authorization": "Bearer token"},
            )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["new_course_progress_percent"] == 0  # Defaults to 0