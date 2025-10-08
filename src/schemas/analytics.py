from typing import Optional

from pydantic import BaseModel, Field


class TrackEventRequest(BaseModel):
    activity_type: str = Field(..., min_length=1, max_length=50)
    details: Optional[dict] = None


class DailyActivity(BaseModel):
    date: str = Field(..., min_length=1, max_length=10)
    activity_count: int = Field(..., ge=0)


class ActivityDetailsResponse(BaseModel):
    activities: list[DailyActivity]