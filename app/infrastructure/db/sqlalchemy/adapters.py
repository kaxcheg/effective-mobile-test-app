from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable, ClassVar, TypeVar, override

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
)

from app.application.dto import CredentialDTO, UserSessionDTO
from app.application.exceptions import (
    IntegrityUserError,
    NotAuthenticatedError,
    NotAuthorizedError,
    ConcurrencyError
)
from app.application.ports.services import AuthorizeService
from app.application.ports.uow import UnitOfWork
from app.domain.entities.base import Repository
from app.domain.entities.user import User
from app.domain.entities.user.repo import UserRepository
from app.domain.services import UserIdGenerator
from app.domain.value_objects import UserId, Username, UserPasswordHash, UserRole, Email
from app.infrastructure.db.sqlalchemy.models.user import UserORM
from app.infrastructure.security.jwt_service import (
    JwtTokenExpired,
    JwtTokenInvalid,
    JwtTokenService,
)

type RepoFactory[R: Repository] = Callable[[AsyncSession], R]


class UserRepositorySQL(UserRepository):
    """SQLAlchemy repository that maps Domain to ORM and back."""

    def __init__(self, session: AsyncSession) -> None:
        """Store session bound to current UoW transaction."""
        self._s = session

    @override
    async def get_by_id(self, user_id: UserId) -> User | None:
        """Return a user by id or None."""
        result = await self._s.get(UserORM, user_id.value)
        if result is None:
            return None
        return User.from_storage(
            id=UserId(result.id),
            username=Username(result.username),
            email=Email(result.email),
            password_hash=UserPasswordHash(result.password_hash),
            role=UserRole(result.role),
            is_active=result.is_active,
        )

    @override
    async def get_by_email(self, email: Email) -> User | None:
        """Return a user by email or None."""
        result = await self._s.scalars(
            select(UserORM).where(UserORM.email == str(email))
        )
        row = result.first()
        if row is None:
            return None
        return User.from_storage(
            id=UserId(row.id),
            email=Email(row.email),
            username=Username(row.username),
            password_hash=UserPasswordHash(row.password_hash),
            role=UserRole(row.role),
            is_active=row.is_active,
        )

    @override
    async def add(self, user: User) -> None:
        """Persist a new user or raise on conflict."""
        user_orm = UserORM(
            id=user.id.value,
            username=str(user.username),
            email=str(user.email),
            password_hash=user.password_hash.value,
            role=str(user.role),
            is_active=user.is_active,
        )
        try:
            self._s.add(user_orm)
            await self._s.flush()
        except IntegrityError as e:
            raise IntegrityUserError(f"Integrity error occured when adding {user_orm.id}") from e

    @override
    async def save(self, user: User) -> User:
        stmt = update(UserORM).where(UserORM.id==user.id.value).values(
            email=user.email.value,
            username=user.username.value,
            role=user.role,
            is_active=user.is_active,
            password_hash=user.password_hash.value
        ).returning(UserORM)
        try:
            res = await self._s.execute(stmt)
            rows = res.scalars().all()
        except IntegrityError as e:
            raise IntegrityUserError(f"Integrity error occured when adding {user.id.value}") from e
        if len(rows) != 1:
            raise ConcurrencyError("User was modified concurrently")
        return User.from_storage(
            id=UserId(rows[0].id),
            username=Username(rows[0].username),
            email=Email(rows[0].email),
            password_hash=UserPasswordHash(rows[0].password_hash),
            role=UserRole(rows[0].role)
        )


R = TypeVar("R", bound=Repository)


class UoWSQL(UnitOfWork):
    """Unit-of-Work adapter for async SQLAlchemy."""

    _REGISTRY: ClassVar[dict[Repository, RepoFactory[Repository]]] = {
        UserRepository: lambda s: UserRepositorySQL(s),
    }

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with session factory."""
        self._sf = session_factory
        self._session: AsyncSession | None = None
        self._txn: AsyncSessionTransaction | None = None

    @override
    async def _open(self) -> None:
        """Begin a new transactional session."""
        self._session = self._sf()
        self._txn = await self._session.begin()

    @override
    async def commit(self) -> None:
        """Commit active transaction."""
        assert self._txn is not None, "No transaction started"
        await self._txn.commit()

    @override
    async def rollback(self) -> None:
        """Rollback active transaction."""
        assert self._txn is not None, "No transaction started"
        await self._txn.rollback()

    @override
    async def _close(self) -> None:
        """Close session safely."""
        if self._session is not None:
            await self._session.close()

    @override
    def get_repo(self, iface: type[R]) -> R:
        """Return repository instance bound to current session.

        Args:
            iface: Repository interface to resolve.

        Returns:
            R: Repository bound to the active session.
        """
        assert self._session is not None, "No session opened"
        try:
            factory = self._REGISTRY[iface]
        except KeyError as e:
            raise KeyError(f"Repository not registered: {iface!r}") from e

        repo = factory(self._session)

        # Safe cast: registry binds factory to iface type.
        from typing import cast

        return cast(R, repo)


class UUIDv4Generator(UserIdGenerator):
    """Id generator that produces UUIDv4 values."""

    @override
    def new(self) -> UserId:
        """Return a new UserId."""
        return UserId(uuid.uuid4())


class RoleAuthService(AuthorizeService):
    """Auth facade using JWT and SQL repository."""


    @override
    def ensure_role(
        self, user_id: UserId, user_role: UserRole, required_roles: list[UserRole]
    ) -> None:
        """Raise when role is insufficient."""
        if user_role in required_roles:
            return
        raise NotAuthorizedError("Forbidden")
