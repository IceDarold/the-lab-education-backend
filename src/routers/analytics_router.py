from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import TrackEventRequest
from src.dependencies import get_db, get_current_user
from src.models.user import User
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/activity-log", tags=["Analytics"])


@router.post("", status_code=202)
async def track_user_activity(
    event_data: TrackEventRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Add the tracking task to background tasks
    background_tasks.add_task(
        AnalyticsService.track_activity,
        user_id=current_user.id,
        event_data=event_data,
        db=db
    )
    # Return immediately with 202 Accepted
    return