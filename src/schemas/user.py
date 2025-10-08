from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class User(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: str = "student"


class CheckEmailRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str


class UserFilter(BaseModel):
    search: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    sort_by: str = "id"
    sort_order: str = "asc"
    skip: int = 0
    limit: int = 10

