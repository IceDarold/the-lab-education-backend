from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class TrackEventRequest(BaseModel):
    activity_type: str = Field(..., min_length=1, max_length=50)
    details: Optional[dict] = None


class DailyActivity(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: str = Field(..., min_length=1, max_length=10)
    LOGIN: Optional[int] = None
    LESSON_COMPLETED: Optional[int] = None
    QUIZ_ATTEMPT: Optional[int] = None
    CODE_EXECUTION: Optional[int] = None

    @model_validator(mode="after")
    def validate_extra_fields(self):
        extra = self.model_extra or {}
        for key, value in extra.items():
            if value is not None and not isinstance(value, int):
                raise ValueError(f"Activity count for '{key}' must be an integer or None")
        return self

    def __getattr__(self, item: str):
        extra = self.model_extra or {}
        if item in extra:
            return extra[item]
        if item in {"model_extra", "__pydantic_extra__"}:
            raise AttributeError(item)
        return None


class ActivityDetailsResponse(BaseModel):
    activities: list[DailyActivity]
