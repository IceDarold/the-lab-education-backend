from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from src.models.user_activity_log import ActivityTypeEnum
import re


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)  # RFC 5321 limit
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    role: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=254)
    role: str
    status: str
    registration_date: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LessonCompleteRequest(BaseModel):
    course_slug: str = Field(..., min_length=1, max_length=100)

    @field_validator('course_slug')
    @classmethod
    def validate_course_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Course slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class TrackEventRequest(BaseModel):
    activity_type: ActivityTypeEnum
    details: Dict[str, Any] | None = None


class UserFilter(BaseModel):
    search: str | None = Field(None, max_length=100)
    role: str | None = None
    status: str | None = None
    sort_by: str = "registration_date"
    sort_order: str = "desc"
    skip: int = 0
    limit: int = 100


class DailyActivity(BaseModel):
    date: str
    LOGIN: Optional[int] = None
    LESSON_COMPLETED: Optional[int] = None
    QUIZ_ATTEMPT: Optional[int] = None
    CODE_EXECUTION: Optional[int] = None


class ActivityDetailsResponse(BaseModel):
    activities: List[DailyActivity]
