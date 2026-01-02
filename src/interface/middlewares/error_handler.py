from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import (
    DomainException,
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    InsufficientDataException,
)
from src.core.logger import app_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes et headers"""
    async def dispatch(self, request: Request, call_next):
        # Logger les headers d'authentification pour le débogage
        auth_header = request.headers.get("authorization")
        if auth_header:
            app_logger.info(f"Authorization header present: {auth_header[:30]}...")
        else:
            app_logger.warning(f"No Authorization header in request to {request.url.path}")
        
        response = await call_next(request)
        return response

def add_exception_handlers(app: FastAPI):
    """Ajoute les gestionnaires d'exceptions"""
    
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        """Gère les exceptions du domaine"""
        app_logger.error(f"Domain exception: {exc.message}", extra={"details": exc.details})
        
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, NotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, UnauthorizedException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, InsufficientDataException):
            status_code = status.HTTP_400_BAD_REQUEST
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Gère les erreurs de validation Pydantic"""
        app_logger.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Gère les HTTPException (notamment les erreurs 401)"""
        # Logger les erreurs d'authentification avec plus de détails
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            app_logger.error(
                f"Authentication failed: {exc.detail}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                }
            )
        else:
            app_logger.warning(
                f"HTTP exception: {exc.detail}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code,
                }
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
            headers=exc.headers,
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Gère les exceptions non attrapées"""
        app_logger.error("Unhandled exception", exc_info=exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        )