from __future__ import annotations

from typing import List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator


class LessonPublic(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = None


class LessonWithStatus(LessonPublic):
    lesson_id: UUID
    slug: str
    status: str


class ModulePublic(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    order: Optional[int] = None
    lessons: List[LessonPublic] = Field(default_factory=list)


class ModuleWithProgress(ModulePublic):
    lessons: List[LessonWithStatus]


class CoursePublic(BaseModel):
    course_id: UUID
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    cover_image_url: Optional[str] = Field(None, max_length=500)

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class CourseWithProgress(CoursePublic):
    progress_percent: int


class CourseDetailsWithProgress(BaseModel):
    title: str
    overall_progress_percent: int
    modules: List[ModuleWithProgress]


class CourseDetailsPublic(BaseModel):
    course_id: UUID
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    modules: List[ModulePublic]

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v