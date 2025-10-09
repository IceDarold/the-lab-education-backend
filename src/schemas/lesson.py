from typing import Any, Dict, List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict


class LessonCell(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., min_length=1, max_length=50)
    content: str
    config: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def cell_type(self) -> str:
        """Backward compatible accessor for the cell type."""
        return self.type

    @property
    def metadata(self) -> Dict[str, Any]:
        """Backward compatible alias for config payload."""
        return self.config


class Lesson(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    cells: List[LessonCell] = Field(default_factory=list)


class LessonContent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
