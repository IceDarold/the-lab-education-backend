from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class CreateCourseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class CreateModuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    parent_slug: str = Field(..., min_length=1, max_length=100)

    @field_validator('slug', 'parent_slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v


class CreateLessonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    parent_slug: str = Field(..., min_length=1, max_length=100)

    @field_validator('slug', 'parent_slug')
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v
