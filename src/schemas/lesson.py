from typing import Any, Dict, List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator


class LessonCell(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    content: str
    config: Dict[str, Any] = Field(default_factory=dict)


class Lesson(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    cells: List[LessonCell] = Field(default_factory=list)


class LessonContent(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    course_slug: Optional[str] = Field(None, min_length=1, max_length=100)
    lesson_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cells: List[LessonCell] = Field(default_factory=list)

    @field_validator('slug', 'course_slug')
    @classmethod
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class LessonCompleteRequest(BaseModel):
    course_slug: str = Field(..., min_length=1, max_length=100)

    @field_validator('course_slug')
    @classmethod
    def validate_course_slug(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Course slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class LessonCompleteResponse(BaseModel):
    new_course_progress_percent: int