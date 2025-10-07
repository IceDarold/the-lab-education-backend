from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import get_current_user
from src.db.session import get_supabase_client
from src.schemas.course import CourseDetailsPublic, CoursePublic
from src.schemas.user import User

router = APIRouter()


async def _finalize(result):
    execute = getattr(result, "execute", None)
    if callable(execute):
        result = execute()
    if hasattr(result, "__await__"):
        result = await result
    return result


@router.post("/{slug}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_in_course(slug: str, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    supabase = get_supabase_client()

    course_query = supabase.table("courses").select("id").eq("slug", slug).single()
    course_response = await _finalize(course_query)
    course_data = getattr(course_response, "data", course_response)

    if not course_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    course_id = course_data.get("id") if isinstance(course_data, dict) else None
    if not course_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment_payload = {
        "user_id": str(current_user.user_id),
        "course_id": course_id,
    }

    enroll_action = supabase.table("enrollments").insert(enrollment_payload)
    await _finalize(enroll_action)

    return {"status": "enrolled"}


@router.get("", response_model=List[CoursePublic])
async def list_courses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    supabase = get_supabase_client()
    query = (
        supabase.table("courses")
        .select("id, slug, title, description, cover_image_url, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    resp = await _finalize(query)
    data = getattr(resp, "data", resp) or []

    normalized = []
    for row in data:
        normalized.append(
            {
                "course_id": row.get("id"),
                "slug": row.get("slug"),
                "title": row.get("title"),
                "description": row.get("description") or row.get("summary"),
                "cover_image_url": row.get("cover_image_url"),
            }
        )

    return normalized


@router.get("/{slug}", response_model=CourseDetailsPublic)
async def get_course_details(slug: str):
    supabase = get_supabase_client()
    resp = await _finalize(supabase.rpc("get_public_course_details", {"slug": slug}))
    data = getattr(resp, "data", resp)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return data
