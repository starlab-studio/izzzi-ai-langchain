from typing import Any, Optional

class DomainException(Exception):
    """Base exception for the domain"""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class NotFoundException(DomainException):
    """Entity not found"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "NOT_FOUND", details)

class ValidationException(DomainException):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class UnauthorizedException(DomainException):
    """Unauthorized access"""
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(message, "UNAUTHORIZED", details)

class InsufficientDataException(DomainException):
    """Not enought data"""
    def __init__(self, message: str, min_required: int, actual: int):
        super().__init__(
            message,
            "INSUFFICIENT_DATA",
            {"min_required": min_required, "actual": actual}
        )