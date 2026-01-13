"""Custom API exceptions."""
from fastapi import HTTPException, status


class ErrorMessages:
    """Centralized error messages."""

    # Resource not found errors
    SUBSCRIPTION_NOT_FOUND = "Subscription not found"
    USER_NOT_FOUND = "User not found"

    # Validation errors
    INVALID_DATE_FORMAT = "Invalid date format"
    DATE_IN_PAST = "Date cannot be in the past"
    INVALID_AMOUNT = "Amount must be greater than 0"
    INVALID_PERIOD = "Period must be between 1 and 365 days"
    NOTIFY_DAYS_EXCEED_PERIOD = "Notify days cannot exceed period"

    # Generic errors
    RESOURCE_NOT_FOUND = "Resource not found"
    BAD_REQUEST = "Bad request"


class NotFoundException(HTTPException):
    """Resource not found exception."""

    def __init__(self, detail: str = ErrorMessages.RESOURCE_NOT_FOUND):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    """Bad request exception."""

    def __init__(self, detail: str = ErrorMessages.BAD_REQUEST):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
