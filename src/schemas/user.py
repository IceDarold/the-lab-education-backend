from uuid import UUID
from typing import Optional, List
from email_validator import validate_email, EmailNotValidError

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        try:
            # Use email-validator library for robust validation
            valid = validate_email(v)
            return valid.email  # Return normalized email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email format: {str(e)}')


class User(BaseModel):
    user_id: UUID
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    role: str = "student"

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        try:
            # Use email-validator library for robust validation
            valid = validate_email(v)
            return valid.email  # Return normalized email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email format: {str(e)}')


class CheckEmailRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        try:
            # Use email-validator library for robust validation
            valid = validate_email(v)
            return valid.email  # Return normalized email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email format: {str(e)}')


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=254)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        try:
            # Use email-validator library for robust validation
            valid = validate_email(v)
            return valid.email  # Return normalized email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email format: {str(e)}')


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=1000)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    role: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            try:
                # Use email-validator library for robust validation
                valid = validate_email(v)
                return valid.email  # Return normalized email
            except EmailNotValidError as e:
                raise ValueError(f'Invalid email format: {str(e)}')
        return v


class UserResponse(BaseModel):
    id: int
    user_id: UUID
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    role: str = "student"
    created_at: str
    updated_at: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        try:
            # Use email-validator library for robust validation
            valid = validate_email(v)
            return valid.email  # Return normalized email
        except EmailNotValidError as e:
            raise ValueError(f'Invalid email format: {str(e)}')


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
    sort_by: str = "id"
    sort_order: str = "asc"
    skip: int = 0
    limit: int = 10