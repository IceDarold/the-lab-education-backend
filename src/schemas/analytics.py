from typing import Optional

from pydantic import BaseModel, Field


class TrackEventRequest(BaseModel):
    activity_type: str = Field(..., min_length=1, max_length=50)
    details: Optional[dict] = None