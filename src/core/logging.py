import sys
from contextvars import ContextVar
from loguru import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

# Context variable for request ID
request_id_context: ContextVar[str] = ContextVar('request_id', default='')

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Set the request ID in context
        request_id_context.set(request_id)

        # Add request ID to request state for access in handlers
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id

        return response

def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_context.get()

def setup_logging():
    """Configure structured logging with loguru."""

    # Remove default handler
    logger.remove()

    # Add structured JSON handler for production
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[request_id]} | {name}:{function}:{line} | {message}",
        level="INFO",
        serialize=False,  # Set to True for JSON output in production
        enqueue=True,  # Async logging
        backtrace=True,
        diagnose=True
    )

    # Add error file handler
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {extra[request_id]} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="1 week",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    # Add access log handler
    logger.add(
        "logs/access.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | ACCESS | {extra[request_id]} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="1 week",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("access", False)
    )

    return logger

# Global logger instance
app_logger = setup_logging()

def get_logger(name: str):
    """Get a logger instance with the given name."""
    return app_logger.bind(request_id=get_request_id())

# Create logs directory if it doesn't exist
import os
os.makedirs("logs", exist_ok=True)