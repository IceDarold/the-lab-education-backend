import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from src.main import app


@pytest.mark.asyncio
async def test_register_user_success(monkeypatch):
    client_mock = MagicMock()
    sign_up_response = MagicMock()
    sign_up_response.session = MagicMock(access_token="fake-register-token")
    client_mock.auth = MagicMock()
    client_mock.auth.sign_up = AsyncMock(return_value=sign_up_response)

    profiles_table = MagicMock()
    profiles_table.insert = AsyncMock(return_value=MagicMock())
    client_mock.table = MagicMock(return_value=profiles_table)

    try:
        monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: client_mock)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "full_name": "Test User",
            "email": "user@example.com",
            "password": "supersecret",
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)

    assert response.status_code in {200, 201}
    data = response.json()
    assert data.get("access_token") == "fake-register-token"


@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    client_mock = MagicMock()
    sign_in_response = MagicMock()
    sign_in_response.session = MagicMock(access_token="fake-login-token")
    client_mock.auth = MagicMock()
    client_mock.auth.sign_in_with_password = AsyncMock(return_value=sign_in_response)

    try:
        monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: client_mock)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        form_data = {
            "username": "user@example.com",
            "password": "supersecret",
        }
        response = await async_client.post(
            "/api/v1/auth/login",
            data=form_data,
        )

    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token") == "fake-login-token"


@pytest.mark.asyncio
async def test_get_me_success(monkeypatch):
    client_mock = MagicMock()
    user_id = "11111111-1111-1111-1111-111111111111"
    user_data = MagicMock()
    user_data.id = user_id
    user_data.email = "user@example.com"
    user_data.user_metadata = {"full_name": "Test User"}

    get_user_response = MagicMock(user=user_data)

    client_mock.auth = MagicMock()
    client_mock.auth.get_user = AsyncMock(return_value=get_user_response)

    try:
        monkeypatch.setattr("src.core.security.get_supabase_client", lambda: client_mock)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data.get("user_id") == user_id
    assert data.get("email") == "user@example.com"
    assert data.get("full_name") == "Test User"
