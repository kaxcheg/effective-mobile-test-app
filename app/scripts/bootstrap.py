#!/usr/bin/env python3
"""Creates admin user with APP_ADMIN, APP_ADMIN_PASSWORD_HASH envs"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.exceptions import IntegrityUserError
from app.application.ports.uow import UnitOfWork
from app.config import get_settings
from app.domain.entities.user import User
from app.domain.entities.user.repo import UserRepository
from app.domain.exceptions.base import DomainError
from app.domain.value_objects import Username, UserPasswordHash, UserRole, Email
from app.infrastructure.db.sqlalchemy.adapters import UoWSQL, UUIDv4Generator

cfg = get_settings()
engine = create_async_engine(str(cfg.DB_URL), pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def uow_factory() -> UnitOfWork:
    """Return UnitOfWork bound to the async session."""
    return UoWSQL(async_session)


async def main() -> int:
    """Bootstrap: create an admin user once"""

    username = cfg.EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_USERNAME
    password_hash = (
        cfg.EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_PASSWORD_HASH.get_secret_value()
    )
    email = cfg.EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_EMAIL

    if not username or not password_hash or not email:
        sys.exit(
            "[effective_mobile_test_app_bootstrap] EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_USERNAME, "
            "EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_EMAIL,"
            "EFFECTIVE_MOBILE_TEST_APP_BOOTSTRAP_ADMIN_PASSWORD_HASH, must be set"
        )

    try:
        user = User.create(
            username=Username(username),
            email=Email(email),
            password_hash=UserPasswordHash(value=password_hash.encode()),
            role=UserRole.ADMIN,
            id_gen=UUIDv4Generator(),
        )
    except (DomainError, ValueError) as e:
        sys.exit(
            f"[effective_mobile_test_app_bootstrap] User with provided parameters cannot be created: {e}"
        )

    try:
        async with uow_factory() as uow:
            repo: UserRepository = uow.get_repo(UserRepository)
            await repo.add(user)
    except IntegrityUserError:
        print("[effective_mobile_test_app_bootstrap] User already exists")
        sys.exit(0)

    print(
        f"[effective_mobile_test_app_bootstrap] Admin created (id={user.id}, user={user.username})"
    )
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
