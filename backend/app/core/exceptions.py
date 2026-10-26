class AppException(Exception):
    """Base exception."""

class UserAlreadyExistsError(AppException):
    """User already exists."""

class InvalidCredentialsError(AppException):
    """Invalid username or password."""

class VideoNotFoundError(AppException):
    """Video not found."""

class InactiveUserError(AppException):
    """User account is deactivated."""

class InvalidJobStatusTransitionError(AppException):
    """Requested processing job status transition is not allowed."""