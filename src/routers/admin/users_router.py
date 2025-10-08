from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from math import ceil
from src.services.user_service import UserService
from src.services.progress_service import ProgressService
from src.services.analytics_service import AnalyticsService
from src.services.content_scanner_service import ContentScannerService
from src.schemas import UsersListResponse, UserResponse
from src.dependencies import get_db, get_current_admin
from src.models.user import User
from src.models.enrollment import Enrollment

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("/", response_model=UsersListResponse)
async def list_users(
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    sort_by: str = "registrationDate",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    users = await UserService.list_users(
        db=db,
        search=search,
        role=role,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )

    # Count total items
    count_query = select(func.count()).select_from(User)
    if search:
        from sqlalchemy import or_, text
        count_query = count_query.where(
            or_(
                User.fullName.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    if role:
        count_query = count_query.where(User.role == role)
    if status:
        count_query = count_query.where(User.status == status)

    result = await db.execute(count_query)
    total_items = result.scalar()

    total_pages = ceil(total_items / limit) if limit > 0 else 0
    current_page = skip // limit + 1

    return UsersListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total_items=total_items,
        total_pages=total_pages,
        current_page=current_page,
        page_size=limit,
    )


@router.get("/{user_id}/details")
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    content_scanner: ContentScannerService = Depends(get_content_scanner),
):
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get enrolled courses
    enroll_query = select(Enrollment.course_slug).where(Enrollment.user_id == user_id)
    enroll_result = await db.execute(enroll_query)
    enrolled_courses = [row.course_slug for row in enroll_result]

    # Get progress for each course
    progress = {}
    for course_slug in enrolled_courses:
        progress_data = await ProgressService.get_user_progress_for_course(
            user_id=user_id,
            course_slug=course_slug,
            db=db,
            content_service=content_scanner,
        )
        progress[course_slug] = progress_data

    # Get activity details
    activity = await AnalyticsService.get_activity_details(user_id=user_id, db=db)

    return {
        "user": UserResponse.from_orm(user),
        "activity": activity,
        "progress": progress,
    }