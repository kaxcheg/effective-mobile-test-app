# auth/ports.py
from __future__ import annotations
from typing import Any, Mapping, Protocol, Optional
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User
from app.domain.value_objects import UserId

class TokenService(Protocol):
    def issue(
        self,
        claims: Mapping[str, Any],
        *,
        expires_in: timedelta | int | None = None,
        additional_headers: Mapping[str, Any] | None = None,
    ) -> str: ...
    def decode(self, token: str, *, verify_exp: bool = True) -> dict[str, Any]: ...

class AuthenticateService(Protocol):
    async def get_user_by_session_id(self, db: AsyncSession, session_id: UUID) -> Optional[User]: ...
    async def delete_user_session_by_user_id(self, db: AsyncSession, user_id: UserId) -> None: ...
