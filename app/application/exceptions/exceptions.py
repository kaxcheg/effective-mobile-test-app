from app.application.exceptions.base import ApplicationError


class IntegrityUserError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, if adding to repo existing user."""


class NotAuthenticatedError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, if user is not authenticated."""


class NotAuthorizedError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, if user is not authorized."""

class DuplicateUserSessionError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, if adding to repo existing user session."""

class NotFoundUserSessionError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, when checking user session."""

class ConcurrencyError(ApplicationError):
    """Adapters should raise and use cases should handle this exception, when concurrency errors occur."""
