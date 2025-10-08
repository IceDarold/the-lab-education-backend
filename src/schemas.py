from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.user_activity_log import ActivityTypeEnum


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    status: str
    registration_date: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LessonCompleteRequest(BaseModel):
    course_slug: str


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
    search: str | None = None
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