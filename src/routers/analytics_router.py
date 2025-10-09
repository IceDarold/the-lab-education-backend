from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.schemas import TrackEventRequest, ActivityDetailsResponse
from src.dependencies import get_db, require_current_user
from src.models.user import User
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/activity-log", tags=["Analytics"])


@router.post("", status_code=202)
async def track_user_activity(
    event_data: TrackEventRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    # Add the tracking task to background tasks
    background_tasks.add_task(
        AnalyticsService.track_activity,
        user_id=current_user.user_id,
        event_data=event_data,
        db=db
    )
    # Return immediately with 202 Accepted
    return
@router.get("", response_model=ActivityDetailsResponse)
async def get_user_activity_details(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
) -> ActivityDetailsResponse:
    activities = await AnalyticsService.get_activity_details(current_user.user_id, db)
    return ActivityDetailsResponse(activities=activities)
