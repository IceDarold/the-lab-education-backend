import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.mark.asyncio
async def test_register_user_success(async_client, mock_supabase_client, monkeypatch):
    sign_up_response = MagicMock()
    sign_up_response.session = MagicMock(access_token="fake-register-token")
    mock_supabase_client.auth.sign_up = AsyncMock(return_value=sign_up_response)

    profiles_table = MagicMock()
    profiles_table.insert = AsyncMock(return_value=MagicMock())
    mock_supabase_client.table = MagicMock(return_value=profiles_table)

    try:
        monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: mock_supabase_client)

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
async def test_login_success(async_client, mock_supabase_client, monkeypatch):
    sign_in_response = MagicMock()
    sign_in_response.session = MagicMock(access_token="fake-login-token")
    mock_supabase_client.auth.sign_in_with_password = AsyncMock(return_value=sign_in_response)

    try:
        monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: mock_supabase_client)

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
async def test_get_me_success(async_client, mock_supabase_client, monkeypatch):
    user_id = "11111111-1111-1111-1111-111111111111"
    user_data = MagicMock()
    user_data.id = user_id
    user_data.email = "user@example.com"
    user_data.user_metadata = {"full_name": "Test User"}

    get_user_response = MagicMock(user=user_data)

    mock_supabase_client.auth.get_user = AsyncMock(return_value=get_user_response)

    try:
        monkeypatch.setattr("src.core.security.get_supabase_client", lambda: mock_supabase_client)
    except AttributeError:
        monkeypatch.setattr("src.db.session.get_supabase_client", lambda: mock_supabase_client)

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data.get("user_id") == user_id
    assert data.get("email") == "user@example.com"
    assert data.get("full_name") == "Test User"


@pytest.mark.asyncio
async def test_check_email_exists(async_client, mock_supabase_admin_client, monkeypatch):
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(return_value=MagicMock(data=[{"id": "some-id"}]))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)

    payload = {"email": "user@example.com"}
    response = await async_client.post("/api/v1/auth/check-email", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("exists") is True


@pytest.mark.asyncio
async def test_check_email_not_exists(async_client, mock_supabase_admin_client, monkeypatch):
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(return_value=MagicMock(data=[]))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)

    payload = {"email": "nonexistent@example.com"}
    response = await async_client.post("/api/v1/auth/check-email", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("exists") is False


@pytest.mark.asyncio
async def test_check_email_database_error(async_client, mock_supabase_admin_client, monkeypatch):
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(side_effect=Exception("Database error"))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)

    payload = {"email": "user@example.com"}
    response = await async_client.post("/api/v1/auth/check-email", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "Database error" in data.get("detail")


@pytest.mark.asyncio
async def test_forgot_password_success(async_client, mock_supabase_admin_client, mock_supabase_client, monkeypatch):
    # Mock admin client for checking email
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(return_value=MagicMock(data=[{"id": "some-id"}]))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    # Mock regular client for sending email
    mock_supabase_client.auth.reset_password_for_email = AsyncMock()

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)
    monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)

    payload = {"email": "user@example.com"}
    response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Password reset email sent"


@pytest.mark.asyncio
async def test_forgot_password_email_not_found(async_client, mock_supabase_admin_client, monkeypatch):
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(return_value=MagicMock(data=[]))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)

    payload = {"email": "nonexistent@example.com"}
    response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Email not found" in data.get("detail")


@pytest.mark.asyncio
async def test_forgot_password_database_error(async_client, mock_supabase_admin_client, monkeypatch):
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(side_effect=Exception("Database error"))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)

    payload = {"email": "user@example.com"}
    response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "Database error" in data.get("detail")


@pytest.mark.asyncio
async def test_forgot_password_send_email_error(async_client, mock_supabase_admin_client, mock_supabase_client, monkeypatch):
    # Mock admin client for checking email
    profiles_table = MagicMock()
    select_mock = MagicMock()
    select_mock.eq = MagicMock(return_value=select_mock)
    select_mock.execute = AsyncMock(return_value=MagicMock(data=[{"id": "some-id"}]))
    profiles_table.select = MagicMock(return_value=select_mock)
    mock_supabase_admin_client.table = MagicMock(return_value=profiles_table)

    # Mock regular client for sending email with error
    mock_supabase_client.auth.reset_password_for_email = AsyncMock(side_effect=Exception("Send error"))

    monkeypatch.setattr("src.api.v1.auth.get_supabase_admin_client", lambda: mock_supabase_admin_client)
    monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)

    payload = {"email": "user@example.com"}
    response = await async_client.post("/api/v1/auth/forgot-password", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "Failed to send reset email" in data.get("detail")


@pytest.mark.asyncio
async def test_reset_password_success(async_client, mock_supabase_client, monkeypatch):
    mock_supabase_client.auth.verify_otp = AsyncMock()
    mock_supabase_client.auth.update_user = AsyncMock()

    monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)

    payload = {"token": "valid-token", "new_password": "newpassword123"}
    response = await async_client.post("/api/v1/auth/reset-password", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Password updated successfully"


@pytest.mark.asyncio
async def test_reset_password_invalid_token(async_client, mock_supabase_client, monkeypatch):
    mock_supabase_client.auth.verify_otp = AsyncMock(side_effect=Exception("Invalid token"))

    monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)

    payload = {"token": "invalid-token", "new_password": "newpassword123"}
    response = await async_client.post("/api/v1/auth/reset-password", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid or expired token" in data.get("detail")


@pytest.mark.asyncio
async def test_reset_password_update_error(async_client, mock_supabase_client, monkeypatch):
    mock_supabase_client.auth.verify_otp = AsyncMock()
    mock_supabase_client.auth.update_user = AsyncMock(side_effect=Exception("Update error"))

    monkeypatch.setattr("src.api.v1.auth.get_supabase_client", lambda: mock_supabase_client)

    payload = {"token": "valid-token", "new_password": "newpassword123"}
    response = await async_client.post("/api/v1/auth/reset-password", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "Failed to update password" in data.get("detail")
