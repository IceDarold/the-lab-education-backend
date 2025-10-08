import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from src.main import app
from src.schemas.user import User


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    return User(
        user_id=uuid4(),
        full_name="Test User",
        email="test@example.com",
        role="student"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = MagicMock()
    answers_table = MagicMock()
    client.table = MagicMock(return_value=answers_table)
    return client, answers_table


@pytest.mark.asyncio
async def test_check_quiz_answer_correct(mock_current_user, mock_supabase_client, monkeypatch):
    """Test successful quiz answer check with correct answer."""
    client_mock, answers_table = mock_supabase_client
    correct_answer_id = str(uuid4())
    question_id = str(uuid4())
    selected_answer_id = correct_answer_id

    # Mock the query chain
    single_mock = MagicMock()
    eq_mock = MagicMock(return_value=single_mock)
    answers_table.eq = MagicMock(return_value=eq_mock)
    single_mock.single = MagicMock(return_value=single_mock)

    # Mock the response
    response_mock = MagicMock()
    response_mock.data = {"correct_answer_id": correct_answer_id}
    single_mock.execute = AsyncMock(return_value=response_mock)

    monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)
    monkeypatch.setattr("src.core.security.get_current_user", lambda: mock_current_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["correct_answer_id"] == correct_answer_id


@pytest.mark.asyncio
async def test_check_quiz_answer_incorrect(mock_current_user, mock_supabase_client, monkeypatch):
    """Test quiz answer check with incorrect answer."""
    client_mock, answers_table = mock_supabase_client
    correct_answer_id = str(uuid4())
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())  # Different from correct

    # Mock the query chain
    single_mock = MagicMock()
    eq_mock = MagicMock(return_value=single_mock)
    answers_table.eq = MagicMock(return_value=eq_mock)
    single_mock.single = MagicMock(return_value=single_mock)

    # Mock the response
    response_mock = MagicMock()
    response_mock.data = {"correct_answer_id": correct_answer_id}
    single_mock.execute = AsyncMock(return_value=response_mock)

    monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)
    monkeypatch.setattr("src.core.security.get_current_user", lambda: mock_current_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["correct_answer_id"] == correct_answer_id


@pytest.mark.asyncio
async def test_check_quiz_answer_question_not_found(mock_current_user, mock_supabase_client, monkeypatch):
    """Test quiz answer check when question is not found."""
    client_mock, answers_table = mock_supabase_client
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain to raise exception
    single_mock = MagicMock()
    eq_mock = MagicMock(return_value=single_mock)
    answers_table.eq = MagicMock(return_value=eq_mock)
    single_mock.single = MagicMock(return_value=single_mock)
    single_mock.execute = AsyncMock(side_effect=Exception("Query failed"))

    monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)
    monkeypatch.setattr("src.core.security.get_current_user", lambda: mock_current_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]


@pytest.mark.asyncio
async def test_check_quiz_answer_database_exception(mock_current_user, mock_supabase_client, monkeypatch):
    """Test quiz answer check with database query exception."""
    client_mock, answers_table = mock_supabase_client
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain to raise exception
    single_mock = MagicMock()
    eq_mock = MagicMock(return_value=single_mock)
    answers_table.eq = MagicMock(return_value=eq_mock)
    single_mock.single = MagicMock(return_value=single_mock)
    single_mock.execute = AsyncMock(side_effect=Exception("Database error"))

    monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)
    monkeypatch.setattr("src.core.security.get_current_user", lambda: mock_current_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]


@pytest.mark.asyncio
async def test_check_quiz_answer_missing_correct_answer_id(mock_current_user, mock_supabase_client, monkeypatch):
    """Test quiz answer check when correct_answer_id is missing."""
    client_mock, answers_table = mock_supabase_client
    question_id = str(uuid4())
    selected_answer_id = str(uuid4())

    # Mock the query chain
    single_mock = MagicMock()
    eq_mock = MagicMock(return_value=single_mock)
    answers_table.eq = MagicMock(return_value=eq_mock)
    single_mock.single = MagicMock(return_value=single_mock)

    # Mock the response with missing correct_answer_id
    response_mock = MagicMock()
    response_mock.data = {}  # No correct_answer_id
    single_mock.execute = AsyncMock(return_value=response_mock)

    monkeypatch.setattr("src.db.session.get_supabase_client", lambda: client_mock)
    monkeypatch.setattr("src.core.security.get_current_user", lambda: mock_current_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        payload = {
            "question_id": question_id,
            "selected_answer_id": selected_answer_id
        }
        response = await async_client.post("/api/v1/quizzes/answers/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Question not found" in data["detail"]