from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.v1 import admin, auth, courses, dashboard, lessons, quizzes
from src.core.errors import (
    ContentFileNotFoundError, SecurityError, ParsingError,
    AuthenticationError, AuthorizationError, ValidationError, DatabaseError, ExternalServiceError
)
from src.core.security import get_current_admin
from src.core.logging import RequestIDMiddleware, app_logger
from src.dependencies import get_fs_service, get_content_scanner, get_ulf_parser


app = FastAPI(title="ML-Practicum API")

# Setup logging
app_logger.info("Starting ML-Practicum API")

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Exception handlers
app.add_exception_handler(ContentFileNotFoundError, lambda request, exc: JSONResponse(status_code=404, content={"detail": "Content not found", "error_code": "CONTENT_NOT_FOUND"}))
app.add_exception_handler(SecurityError, lambda request, exc: JSONResponse(status_code=403, content={"detail": "Access denied", "error_code": "ACCESS_DENIED"}))
app.add_exception_handler(ParsingError, lambda request, exc: JSONResponse(status_code=400, content={"detail": "Invalid content format", "error_code": "PARSING_ERROR"}))
app.add_exception_handler(AuthenticationError, lambda request, exc: JSONResponse(status_code=401, content={"detail": "Authentication failed", "error_code": "AUTHENTICATION_ERROR"}))
app.add_exception_handler(AuthorizationError, lambda request, exc: JSONResponse(status_code=403, content={"detail": "Authorization failed", "error_code": "AUTHORIZATION_ERROR"}))
app.add_exception_handler(ValidationError, lambda request, exc: JSONResponse(status_code=400, content={"detail": str(exc), "error_code": "VALIDATION_ERROR"}))
app.add_exception_handler(DatabaseError, lambda request, exc: JSONResponse(status_code=500, content={"detail": "Database operation failed", "error_code": "DATABASE_ERROR"}))
app.add_exception_handler(ExternalServiceError, lambda request, exc: JSONResponse(status_code=502, content={"detail": "External service unavailable", "error_code": "EXTERNAL_SERVICE_ERROR"}))

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
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(lessons.router, prefix="/api/v1/lessons", tags=["lessons"])
app.include_router(quizzes.router, prefix="/api/v1/quizzes", tags=["quizzes"])
