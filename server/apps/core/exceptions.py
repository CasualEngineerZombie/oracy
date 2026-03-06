"""
Custom exception handlers and exceptions for the Oracy AI API.
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Format the error response
        error_data = {
            "success": False,
            "error": {
                "code": response.status_code,
                "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                "type": exc.__class__.__name__,
            }
        }
        response.data = error_data
    
    return response


class ServiceUnavailableError(APIException):
    """
    Raised when an external service is unavailable.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


class AIProcessingError(APIException):
    """
    Raised when AI processing fails.
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "AI processing failed."
    default_code = "ai_processing_error"


class ValidationError(APIException):
    """
    Raised for validation errors.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed."
    default_code = "validation_error"


class PermissionDeniedError(APIException):
    """
    Raised when user doesn't have permission.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You don't have permission to perform this action."
    default_code = "permission_denied"


class NotFoundError(APIException):
    """
    Raised when a resource is not found.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."
    default_code = "not_found"


class ConflictError(APIException):
    """
    Raised when there's a conflict (e.g., duplicate resource).
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource conflict."
    default_code = "conflict"
