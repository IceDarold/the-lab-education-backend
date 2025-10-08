from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.v1 import admin, auth, courses, dashboard, lessons, quizzes
from src.api.v1 import auth, courses, dashboard, lessons, quizzes
from src.core.errors import FileNotFoundError, SecurityError, ParsingError
from src.core.security import get_current_admin
from src.services.file_system_service import FileSystemService
from src.services.content_scanner_service import ContentScannerService
from src.services.ulf_parser_service import ULFParserService


def get_fs_service() -> FileSystemService:
    return FileSystemService()


def get_content_scanner(fs: FileSystemService = Depends(get_fs_service)) -> ContentScannerService:
    return ContentScannerService(fs)


def get_ulf_parser() -> ULFParserService:
    return ULFParserService()


app = FastAPI(title="ML-Practicum API")

# Exception handlers
app.add_exception_handler(FileNotFoundError, lambda request, exc: JSONResponse(status_code=404, content={"detail": "Not Found"}))
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
# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(lessons.router, prefix="/api/v1/lessons", tags=["lessons"])
app.include_router(quizzes.router, prefix="/api/v1/quizzes", tags=["quizzes"])
