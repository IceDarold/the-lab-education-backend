"""
Test utilities and helper functions for consistent testing patterns.

This module provides centralized utilities for:
- Authentication helpers (test tokens, mock users)
- Database helpers (test data creation, cleanup)
- API helpers (authenticated requests, response parsing)
- Assertion helpers (common response validations)
"""

import json
from typing import Any, Dict, Optional, Union
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.schemas.user import User


# Authentication Helpers
def create_test_user(
    user_id: Optional[str] = None,
    email: str = "test@example.com",
    full_name: str = "Test User",
    role: str = "student"
) -> User:
    """Create a test user object."""
    return User(
        user_id=user_id or str(uuid4()),
        email=email,
        full_name=full_name,
        role=role
    )


def create_mock_authenticated_user(user: Optional[User] = None) -> MagicMock:
    """Create a mock authenticated user for dependency injection."""
    if user is None:
        user = create_test_user()
    mock_user = MagicMock()
    mock_user.id = user.user_id
    mock_user.email = user.email
    mock_user.full_name = user.full_name
    mock_user.role = user.role
    return mock_user


def create_test_token(user_id: str = "test-user-id", email: str = "test@example.com") -> str:
    """Create a test JWT token."""
    return f"test-token-{user_id}-{email}"


def get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Get authorization headers for authenticated requests."""
    if token is None:
        token = create_test_token()
    return {"Authorization": f"Bearer {token}"}


# Database Helpers
async def create_test_course_data(course_slug: str = "test-course", title: str = "Test Course") -> Dict[str, Any]:
    """Create test course data structure."""
    return {
        "id": str(uuid4()),
        "slug": course_slug,
        "title": title,
        "description": f"Description for {title}",
        "cover_image_url": "https://example.com/image.jpg",
        "created_at": "2023-01-01T00:00:00Z"
    }


async def create_test_lesson_data(
    lesson_slug: str = "test-lesson",
    title: str = "Test Lesson",
    course_slug: str = "test-course"
) -> Dict[str, Any]:
    """Create test lesson data structure."""
    return {
        "lesson_id": str(uuid4()),
        "slug": lesson_slug,
        "title": title,
        "course_slug": course_slug,
        "content": "Test lesson content",
        "created_at": "2023-01-01T00:00:00Z"
    }


def mock_db_response(data: Any) -> MagicMock:
    """Create a mock database response."""
    mock_response = MagicMock()
    mock_response.data = data
    return mock_response


def mock_supabase_query(data: Any = None) -> MagicMock:
    """Create a mock Supabase query chain."""
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.range.return_value = query
    query.single.return_value = query
    query.execute = AsyncMock(return_value=mock_db_response(data))
    return query


# API Helpers
async def make_authenticated_request(
    client: Union[TestClient, AsyncClient],
    method: str,
    url: str,
    user: Optional[User] = None,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """Make an authenticated API request."""
    headers = get_auth_headers()
    if user:
        # In a real scenario, you'd generate a proper token for the user
        pass

    if isinstance(client, TestClient):
        return client.request(method.upper(), url, headers=headers, json=json_data, **kwargs)
    else:
        return await client.request(method.upper(), url, headers=headers, json=json_data, **kwargs)


async def make_request(
    client: Union[TestClient, AsyncClient],
    method: str,
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """Make an API request without authentication."""
    if isinstance(client, TestClient):
        return client.request(method.upper(), url, json=json_data, **kwargs)
    else:
        return await client.request(method.upper(), url, json=json_data, **kwargs)


def parse_json_response(response) -> Dict[str, Any]:
    """Parse JSON response content."""
    if hasattr(response, 'json'):
        return response.json()
    return json.loads(response.content)


# Assertion Helpers
def assert_success_response(response, expected_status: int = 200) -> Dict[str, Any]:
    """Assert successful response and return parsed data."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    return parse_json_response(response)


def assert_error_response(response, expected_status: int, error_detail: Optional[str] = None):
    """Assert error response."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    if error_detail:
        data = parse_json_response(response)
        assert error_detail in str(data), f"Expected '{error_detail}' in error response"


def assert_validation_error(response, field: Optional[str] = None):
    """Assert validation error response (422)."""
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    if field:
        data = parse_json_response(response)
        errors = data.get("detail", [])
        assert any(error.get("loc", []) and field in str(error["loc"]) for error in errors), \
            f"Expected validation error for field '{field}'"


def assert_unauthorized(response):
    """Assert unauthorized response (401)."""
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def assert_forbidden(response):
    """Assert forbidden response (403)."""
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


def assert_not_found(response):
    """Assert not found response (404)."""
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def assert_created(response):
    """Assert created response (201)."""
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"


def assert_no_content(response):
    """Assert no content response (204)."""
    assert response.status_code == 204, f"Expected 204, got {response.status_code}"


# Common Test Data
def get_test_course_data() -> Dict[str, Any]:
    """Get standard test course data."""
    return {
        "title": "Test Course",
        "slug": "test-course",
        "description": "A test course for testing"
    }


def get_test_lesson_data() -> Dict[str, Any]:
    """Get standard test lesson data."""
    return {
        "title": "Test Lesson",
        "slug": "test-lesson",
        "parent_slug": "test-course"
    }


def get_test_user_data() -> Dict[str, Any]:
    """Get standard test user data."""
    return {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }


# Mock Setup Helpers
def setup_mock_service(service: MagicMock, **methods) -> MagicMock:
    """Setup mock service with specified methods."""
    for method_name, return_value in methods.items():
        if hasattr(service, method_name):
            method = getattr(service, method_name)
            if hasattr(method, '__call__'):
                method.return_value = return_value
    return service


async def setup_mock_async_service(service: MagicMock, **methods) -> MagicMock:
    """Setup mock async service with specified methods."""
    for method_name, return_value in methods.items():
        if hasattr(service, method_name):
            method = getattr(service, method_name)
            if hasattr(method, '__call__'):
                method.return_value = AsyncMock(return_value=return_value)
    return service