from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class User(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr

