from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from collections import defaultdict
from uuid import UUID
from src.models.user_activity_log import UserActivityLog
from src.schemas import TrackEventRequest
from src.core.utils import maybe_await

# Ensure SQLAlchemy relationship dependencies are registered when instantiating models
from src.models import user as _user_model  # noqa: F401
from src.models import enrollment as _enrollment_model  # noqa: F401
from src.models import user_lesson_progress as _progress_model  # noqa: F401


class AnalyticsService:
    @staticmethod
    async def get_activity_details(user_id: UUID, db: AsyncSession) -> list[dict]:
        # Calculate the date one year ago
        one_year_ago = datetime.now() - timedelta(days=365)

        # Build the query
        stmt = (
            select(
                func.date(UserActivityLog.timestamp).label('date'),
                UserActivityLog.activity_type,
                func.count().label('count')
            )
            .where(
                UserActivityLog.user_id == user_id,
                UserActivityLog.timestamp >= one_year_ago
            )
            .group_by(
                func.date(UserActivityLog.timestamp),
                UserActivityLog.activity_type
            )
        )

        # Execute the query
        result = await db.execute(stmt)
        rows = await maybe_await(result.all())

        # Process results into a dictionary grouped by date
        activity_data = defaultdict(dict)
        for row in rows:
            date_str = row.date.isoformat()  # Convert date to string
            activity_type = row.activity_type
            count = row.count
            activity_data[date_str][activity_type] = count

        # Convert to list of dictionaries
        activity_list = []
        for date, activities in activity_data.items():
            day_dict = {'date': date}
            day_dict.update(activities)
            activity_list.append(day_dict)

        # Sort by date
        activity_list.sort(key=lambda x: x['date'])

        return activity_list

    @staticmethod
    async def track_activity(user_id: UUID, event_data: TrackEventRequest, db: AsyncSession):
        # Create a new UserActivityLog instance
        activity_log = UserActivityLog(
            user_id=user_id,
            activity_type=event_data.activity_type,
            details=event_data.details
        )
        # Add to session and commit
        db.add(activity_log)
        await db.commit()
