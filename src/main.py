from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from src.api.v1 import admin, auth, courses, dashboard, lessons, quizzes
from src.routers import health_router
from src.core.errors import (
    ContentFileNotFoundError, SecurityError, ParsingError,
    AuthenticationError, AuthorizationError, ValidationError, DatabaseError, ExternalServiceError
)
from src.core.security import get_current_admin
from src.core.logging import RequestIDMiddleware, app_logger
from src.core.config import settings
from src.core.rate_limiting import limiter
from src.dependencies import get_fs_service, get_content_scanner, get_ulf_parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Validate critical environment variables on startup.
    This ensures the app fails fast if required configuration is missing.
    """
    try:
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

        app_logger.info("Environment validation successful")
        app_logger.info(f"Database URL configured: {settings.DATABASE_URL[:20]}...")
        app_logger.info("Application startup complete")
        yield
    except Exception as exc:
        app_logger.error(f"Startup validation failed: {exc}")
        raise


app = FastAPI(title="ML-Practicum API", lifespan=lifespan)

# Expose limiter on application state so SlowAPI middleware can access it.
app.state.limiter = limiter
app.state.limiter.logger = app_logger

# Setup logging
app_logger.info("Starting ML-Practicum API")

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# Exception handlers
app.add_exception_handler(ContentFileNotFoundError, lambda request, exc: JSONResponse(status_code=404, content={"detail": "Content not found", "error_code": "CONTENT_NOT_FOUND"}))
app.add_exception_handler(SecurityError, lambda request, exc: JSONResponse(status_code=403, content={"detail": "Access denied", "error_code": "ACCESS_DENIED"}))
app.add_exception_handler(ParsingError, lambda request, exc: JSONResponse(status_code=400, content={"detail": "Invalid content format", "error_code": "PARSING_ERROR"}))
app.add_exception_handler(AuthenticationError, lambda request, exc: JSONResponse(status_code=401, content={"detail": "Authentication failed", "error_code": "AUTHENTICATION_ERROR"}))
app.add_exception_handler(AuthorizationError, lambda request, exc: JSONResponse(status_code=403, content={"detail": "Authorization failed", "error_code": "AUTHORIZATION_ERROR"}))
app.add_exception_handler(ValidationError, lambda request, exc: JSONResponse(status_code=400, content={"detail": str(exc), "error_code": "VALIDATION_ERROR"}))
app.add_exception_handler(DatabaseError, lambda request, exc: JSONResponse(status_code=500, content={"detail": "Database operation failed", "error_code": "DATABASE_ERROR"}))
app.add_exception_handler(ExternalServiceError, lambda request, exc: JSONResponse(status_code=502, content={"detail": "External service unavailable", "error_code": "EXTERNAL_SERVICE_ERROR"}))
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(status_code=429, content={"detail": "Too many requests", "error_code": "RATE_LIMIT_EXCEEDED"}))
app.add_exception_handler(
    RequestValidationError,
    lambda request, exc: _handle_validation_error(request, exc)
)


def _handle_validation_error(request, exc: RequestValidationError):
    raw_errors = exc.errors()
    normalized_errors = []
    for error in raw_errors:
        ctx = error.get("ctx")
        if ctx and "error" in ctx and isinstance(ctx["error"], Exception):
            ctx = {**ctx, "error": str(ctx["error"])}
        normalized_errors.append({**error, "ctx": ctx})

    app_logger.warning(f"Validation error for {request.url.path}: {normalized_errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": normalized_errors},
    )

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://the-lab-academy.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


# Routers
app.include_router(health_router.router, prefix="/api/v1", tags=["health"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(lessons.router, prefix="/api/v1/lessons", tags=["lessons"])
app.include_router(quizzes.router, prefix="/api/v1/quizzes", tags=["quizzes"])
