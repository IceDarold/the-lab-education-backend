from uuid import UUID
from typing import Optional
import re

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class User(BaseModel):
    user_id: UUID
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    role: str = "student"

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class CheckEmailRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation regex
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=1000)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserFilter(BaseModel):
    search: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    status: Optional[str] = None
    sort_by: str = "id"
    sort_order: str = "asc"
    skip: int = 0
    limit: int = 10