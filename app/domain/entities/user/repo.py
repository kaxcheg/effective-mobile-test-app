from __future__ import annotations

from app.domain.entities.base import Repository
from app.domain.entities.user import User
from app.domain.value_objects import UserId, Email


class UserRepository(Repository):
    """Repository contract for user entities."""

    async def get_by_email(self, email: Email) -> User | None:
        """Return user by email.

        Args:
            email: Unique email.

        Returns:
            User | None: Found user or None.
        """
        ...

    async def get_by_id(self, user_id: UserId) -> User | None:
        """Return user by identifier.

        Args:
            user_id: Unique identifier.

        Returns:
            User | None: Found user or None.
        """
        ...

    async def add(self, user: User) -> None:
        """Persist user.

        Args:
            user: User domain entity.
        """
        ...
    
    async def save(self, user: User) -> User:
        """Save user.

        Args:
            user: User domain entity.
        """
        ...
