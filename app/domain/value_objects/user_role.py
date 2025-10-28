from enum import StrEnum


class UserRole(StrEnum):
    """All allowed user roles."""

    ADMIN = "admin"
    NANAGER = "manager"
    USER = "user"
