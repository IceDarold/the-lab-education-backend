from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from math import ceil
from src.services.user_service import UserService
from src.services.progress_service import ProgressService
from src.services.analytics_service import AnalyticsService
from src.services.content_scanner_service import ContentScannerService
from src.schemas import UsersListResponse, UserResponse, UserFilter
from src.dependencies import get_db, get_current_admin, get_content_scanner
from src.models.user import User
from src.models.enrollment import Enrollment
from src.core.utils import maybe_await

router = APIRouter(dependencies=[Depends(get_current_admin)])


def get_user_service() -> UserService:
    return UserService()


def get_progress_service() -> ProgressService:
    return ProgressService()


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


@router.get("/", response_model=UsersListResponse)
async def list_users(
    filters: UserFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
):
    users = await user_service.list_users(db=db, filters=filters)

    # Count total items
    count_query = select(func.count()).select_from(User)
    if filters.search:
        from sqlalchemy import or_
        count_query = count_query.where(
            or_(
                User.full_name.ilike(f"%{filters.search}%"),
                User.email.ilike(f"%{filters.search}%")
            )
        )
    if filters.role:
        count_query = count_query.where(User.role == filters.role)
    if filters.status:
        count_query = count_query.where(User.status == filters.status)

    result = await db.execute(count_query)
    total_items = await maybe_await(result.scalar())

    total_pages = ceil(total_items / filters.limit) if filters.limit > 0 else 0
    current_page = filters.skip // filters.limit + 1

    return UsersListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total_items=total_items,
        total_pages=total_pages,
        current_page=current_page,
        page_size=filters.limit,
    )


@router.get("/{user_id}/details")
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    content_scanner: ContentScannerService = Depends(get_content_scanner),
    progress_service: ProgressService = Depends(get_progress_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = await maybe_await(result.scalar_one_or_none())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get enrolled courses
    enroll_query = select(Enrollment.course_slug).where(Enrollment.user_id == user_id)
    enroll_result = await db.execute(enroll_query)
    enrolled_courses = [row.course_slug for row in enroll_result]

    # Get progress for each course
    progress = {}
    for course_slug in enrolled_courses:
        progress_data = await progress_service.get_user_progress_for_course(
            user_id=user_id,
            course_slug=course_slug,
            db=db,
            content_service=content_scanner,
        )
        progress[course_slug] = progress_data

    # Get activity details
    activity = await analytics_service.get_activity_details(user_id=user_id, db=db)

    return {
        "user": UserResponse.from_orm(user),
        "activity": activity,
        "progress": progress,
    }
