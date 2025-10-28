from datetime import timedelta
from functools import lru_cache
from typing import Annotated, Callable

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import CredentialDTO
from app.application.ports.services import AuthorizeService, PasswordHasher, PasswordVerifier
from app.application.ports.uow import UnitOfWork
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.create_user import CreateUserUseCase
from app.application.use_cases.delete_user import DeleteUserUseCase
from app.application.use_cases.update_user import UpdateUserUseCase
from app.application.use_cases.view_orders import ViewOrdersUseCase
from app.application.use_cases.view_payments import ViewPaymentsUseCase
from app.config import get_settings
from app.domain.entities.user import User
from app.domain.entities.user.repo import UserRepository
from app.domain.services.services import UserIdGenerator
from app.infrastructure.db.sqlalchemy.adapters import (
    RoleAuthService,
    UoWSQL,
    UUIDv4Generator,
)
from app.infrastructure.db.sqlalchemy.setup import get_session_factory
from app.infrastructure.security.adapters import BcryptHasher, BcryptPasswordVerifier
from app.infrastructure.security.jwt_service import JwtTokenService
from app.interface.http.auth.adapters import SQLAuthenticateService
from app.interface.http.auth.ports import AuthenticateService, TokenService


security: HTTPBearer = HTTPBearer()


@lru_cache
def get_jwt_service() -> JwtTokenService:
    """Return a cached JwtTokenService instance."""
    cfg = get_settings()
    return JwtTokenService(
        secret=cfg.EFFECTIVE_MOBILE_TEST_APP_JWT_SECRET,
        algorithm=cfg.EFFECTIVE_MOBILE_TEST_APP_JWT_ALGORITHM,
        default_expires=timedelta(
            minutes=cfg.EFFECTIVE_MOBILE_TEST_APP_JWT_TOKEN_EXPIRY_TIME
        ),
        required_claims=("sub", "exp", "role", "sid"),
    )


def get_uow_factory() -> Callable[[], UnitOfWork]:
    """Return factory that creates a new UnitOfWork per call."""
    return lambda: UoWSQL(session_factory=get_session_factory())


def get_hasher() -> PasswordHasher:
    """Return password hasher implementation."""
    return BcryptHasher()


def get_id_gen() -> UserIdGenerator:
    """Return identifier generator implementation."""
    return UUIDv4Generator()


def get_verifier() -> PasswordVerifier:
    """Return password verifier implementation."""
    return BcryptPasswordVerifier()


def get_authenticate_user_uc(
    uow_factory: Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)],
    password_verifier: Annotated[PasswordVerifier, Depends(get_verifier)],
) -> AuthenticateUserUseCase:
    """Return AuthenticateUser use case with injected ports."""
    return AuthenticateUserUseCase(
        uow_factory=uow_factory,
        password_verifier=password_verifier,
    )


def get_authorize_service(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> AuthorizeService:
    """Return AuthService bound to JWT credentials."""

    return RoleAuthService()


def get_create_user_uc(
    request: Request,
    uow_factory: Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)],
    hasher: Annotated[PasswordHasher, Depends(get_hasher)],
    id_gen: Annotated[UserIdGenerator, Depends(get_id_gen)],
    auth_service: Annotated[AuthorizeService, Depends(get_authorize_service)],
) -> CreateUserUseCase:
    """Return CreateUser use case with injected ports."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unexpected error: user was not set with middleware.")
    return CreateUserUseCase(
        auth_service=auth_service,
        user=user,
        uow_factory=uow_factory,
        hasher=hasher,
        id_gen=id_gen,
    )


def get_delete_user_uc(
    request: Request,
    uow_factory: Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)],
    auth_service: Annotated[AuthorizeService, Depends(get_authorize_service)],
) -> DeleteUserUseCase:
    """Return CreateUser use case with injected ports."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unexpected error: user was not set with middleware.")
    return DeleteUserUseCase(
        auth_service=auth_service,
        user=user,
        uow_factory=uow_factory,
    )

def get_update_user_uc(
    request: Request,
    uow_factory: Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)],
    hasher: Annotated[PasswordHasher, Depends(get_hasher)],
    auth_service: Annotated[AuthorizeService, Depends(get_authorize_service)],
) -> UpdateUserUseCase:
    """Return CreateUser use case with injected ports."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unexpected error: user was not set with middleware.")
    return UpdateUserUseCase(
        auth_service=auth_service,
        user=user,
        uow_factory=uow_factory,
        hasher=hasher,
    )


def get_view_orders_uc(
    request: Request,
    auth_service: Annotated[AuthorizeService, Depends(get_authorize_service)],
) -> ViewOrdersUseCase:
    """Return CreateUser use case with injected ports."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unexpected error: user was not set with middleware.")
    return ViewOrdersUseCase(
        auth_service=auth_service,
        user=user,
    )

def get_view_payments_uc(
    request: Request,
    auth_service: Annotated[AuthorizeService, Depends(get_authorize_service)],
) -> ViewPaymentsUseCase:
    """Return CreateUser use case with injected ports."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unexpected error: user was not set with middleware.")
    return ViewPaymentsUseCase(
        auth_service=auth_service,
        user=user,
    )


auth_session_service: AuthenticateService = SQLAuthenticateService()
def get_authnticate_service() -> AuthenticateService:
    return auth_session_service


jwt_service: TokenService = get_jwt_service()