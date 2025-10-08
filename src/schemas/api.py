from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    title: str
    slug: str


class CreateModuleRequest(BaseModel):
    title: str
    slug: str
    parentSlug: str


class CreateLessonRequest(BaseModel):
    title: str
    slug: str
    parentSlug: str