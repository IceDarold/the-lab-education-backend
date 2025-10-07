from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LessonCell(BaseModel):
    cell_type: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LessonContent(BaseModel):
    slug: str
    title: str
    course_slug: Optional[str] = None
    lesson_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cells: List[LessonCell] = Field(default_factory=list)


class LessonCompleteResponse(BaseModel):
    new_course_progress_percent: int
