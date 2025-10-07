from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LessonPublic(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = None


class LessonWithStatus(LessonPublic):
    lesson_id: UUID
    slug: str
    status: str


class ModulePublic(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = None
    lessons: List[LessonPublic] = Field(default_factory=list)


class ModuleWithProgress(ModulePublic):
    lessons: List[LessonWithStatus]


class CoursePublic(BaseModel):
    course_id: UUID
    slug: str
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None


class CourseWithProgress(CoursePublic):
    progress_percent: int


class CourseDetailsWithProgress(BaseModel):
    title: str
    overall_progress_percent: int
    modules: List[ModuleWithProgress]


class CourseDetailsPublic(BaseModel):
    course_id: UUID
    slug: str
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    modules: List[ModulePublic]
