from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import structlog
import uuid

logger = structlog.get_logger()

class DomainException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFound(DomainException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, status_code=404)

class InsufficientPermissions(DomainException):
    def __init__(self, message: str = "Insufficient permissions to perform this action"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)

class ValidationException(DomainException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(code="VALIDATION_FAILED", message=message, status_code=422)

async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("domain_exception", code=exc.code, message=exc.message, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    error_id = str(uuid.uuid4())
    logger.error("unhandled_exception", error_id=error_id, request_id=request_id, exc_info=True)
    import traceback
    with open("error.log", "a") as f:
        f.write(f"\\n--- ERROR {error_id} ---\\n")
        traceback.print_exc(file=f)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id
            }
        }
    )
