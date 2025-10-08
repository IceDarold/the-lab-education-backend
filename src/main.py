from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.v1 import admin, auth, courses, dashboard, lessons, quizzes
from src.core.errors import ContentFileNotFoundError, SecurityError, ParsingError
from src.core.security import get_current_admin
from src.dependencies import get_fs_service, get_content_scanner, get_ulf_parser


app = FastAPI(title="ML-Practicum API")

# Exception handlers
app.add_exception_handler(ContentFileNotFoundError, lambda request, exc: JSONResponse(status_code=404, content={"detail": "Not Found"}))
app.add_exception_handler(SecurityError, lambda request, exc: JSONResponse(status_code=403, content={"detail": "Forbidden"}))
app.add_exception_handler(ParsingError, lambda request, exc: JSONResponse(status_code=400, content={"detail": "Bad Request"}))

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
