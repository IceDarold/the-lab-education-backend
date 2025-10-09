from fastapi import APIRouter, HTTPException
from src.core.supabase_client import check_supabase_health
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health/supabase")
async def supabase_health_check():
    """
    Check Supabase connectivity and health status.
    Returns health status information for monitoring purposes.
    """
    try:
        health_status = await check_supabase_health()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Health check service error"
        )


@router.get("/health")
async def general_health_check():
    """
    General health check endpoint.
    """
    return {"status": "healthy", "service": "the-lab-education-backend"}