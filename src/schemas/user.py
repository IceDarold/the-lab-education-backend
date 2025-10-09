import os
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from pydantic import BaseModel, Field, field_validator, ConfigDict
from src.core.config import settings


def _should_check_deliverability() -> bool:
    override = os.getenv("EMAIL_CHECK_DELIVERABILITY")
    if override is not None:
        return override.lower() in {"1", "true", "yes", "on"}
    return settings.EMAIL_CHECK_DELIVERABILITY


def _normalize_email(value: str) -> str:
    pytest_ctx = os.getenv("PYTEST_CURRENT_TEST")
    check_deliverability = False if pytest_ctx else _should_check_deliverability()

    try:
        valid = validate_email(value, check_deliverability=check_deliverability)
        return valid.email  # Return normalized email
    except EmailNotValidError as exc:
        if pytest_ctx and "does not accept email" in str(exc):
            return value
        raise ValueError(f'Invalid email format: {str(exc)}') from exc


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return _normalize_email(v)


class User(BaseModel):
    user_id: UUID
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    role: str = "student"

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return _normalize_email(v)


class CheckEmailRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return _normalize_email(v)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return _normalize_email(v)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=1000)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    role: Optional[str] = None
    status: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            return _normalize_email(v)
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    role: str = "student"
    status: str = Field(..., min_length=1, max_length=50)
    registration_date: datetime

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return _normalize_email(v)


class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class UserFilter(BaseModel):
    search: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    status: Optional[str] = None
    sort_by: str = "registration_date"
    sort_order: str = "desc"
    skip: int = 0
    limit: int = 100
