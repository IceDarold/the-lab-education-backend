from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    title: str
    slug: str


class CreateModuleRequest(BaseModel):
    title: str
    slug: str
    parent_slug: str


class CreateLessonRequest(BaseModel):
    title: str
    slug: str
    parent_slug: str