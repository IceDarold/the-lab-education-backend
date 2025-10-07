import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.main import app


@pytest.mark.asyncio
async def test_list_courses_success(monkeypatch):
    client_mock = MagicMock()

    table = MagicMock()
    # Chain: select -> order -> range -> execute
    table.select.return_value = table
    table.order.return_value = table
    table.range.return_value = table
    table.execute = AsyncMock(
        return_value=MagicMock(
            data=[
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "slug": "ml-foundations",
                    "title": "ML Foundations",
                    "description": "Intro to ML",
                    "cover_image_url": "https://example/cover.png",
                }
            ]
        )
    )
    client_mock.table.return_value = table

    monkeypatch.setattr("src.api.v1.courses.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/courses?limit=10&offset=0")

    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, list) and len(payload) == 1
    assert payload[0]["course_id"] == "00000000-0000-0000-0000-000000000001"
    assert payload[0]["slug"] == "ml-foundations"
    assert payload[0]["title"] == "ML Foundations"
    assert payload[0]["description"] == "Intro to ML"
    assert payload[0]["cover_image_url"] == "https://example/cover.png"


@pytest.mark.asyncio
async def test_get_course_details_success(monkeypatch):
    client_mock = MagicMock()
    rpc_payload = {
        "course_id": "00000000-0000-0000-0000-000000000001",
        "slug": "ml-foundations",
        "title": "ML Foundations",
        "description": "Intro to ML",
        "cover_image_url": "https://example/cover.png",
        "modules": [
            {
                "title": "Part 1",
                "lessons": [
                    {"title": "What is ML?"},
                    {"title": "History"},
                ],
            }
        ],
    }
    client_mock.rpc = AsyncMock(return_value=MagicMock(data=rpc_payload))

    monkeypatch.setattr("src.api.v1.courses.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/courses/ml-foundations")

    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == "ml-foundations"
    assert data["modules"][0]["lessons"][0]["title"] == "What is ML?"


@pytest.mark.asyncio
async def test_get_course_details_not_found(monkeypatch):
    client_mock = MagicMock()
    client_mock.rpc = AsyncMock(return_value=MagicMock(data=None))
    monkeypatch.setattr("src.api.v1.courses.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/courses/unknown")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_courses_pagination_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/courses?limit=0")
    assert resp.status_code == 422
