from typing import Optional

from pydantic import BaseModel


class TrackEventRequest(BaseModel):
    activity_type: str
    details: Optional[dict] = None