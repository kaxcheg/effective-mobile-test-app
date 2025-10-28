from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, runtime_checkable

from app.domain.entities.base import Repository
from app.domain.entities.user import User
from app.domain.entities.user.repo import UserRepository
from app.domain.value_objects import UserId, UserPasswordHash, UserRawPassword, UserRole

from app.application.dto import CredentialDTO


@runtime_checkable
class PasswordHasher(Protocol):
    """Hash raw password to secure hash."""

    def hash(self, raw_password: UserRawPassword, /) -> UserPasswordHash: ...


@runtime_checkable
class PasswordVerifier(Protocol):
    """Return True when raw password matches stored hash."""

    def verify(
        self, raw_password: UserRawPassword, hashed_password: UserPasswordHash
    ) -> bool: ...


class AuthorizeService(ABC):

    @abstractmethod
    def ensure_role(
        self,
        user_id: UserId,
        user_role: UserRole,
        required_roles: list[UserRole],
    ) -> None: ...
