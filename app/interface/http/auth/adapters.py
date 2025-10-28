# auth/adapters.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, join, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlalchemy.models.user_session import UserSessionORM 
from app.infrastructure.db.sqlalchemy.models.user import UserORM

from app.domain.entities.user import User
from app.domain.value_objects import UserId, Username, Email, UserPasswordHash, UserRole

class SQLAuthenticateService:
    async def get_user_by_session_id(self, db: AsyncSession, session_id: UUID) -> Optional[User]:
        now = datetime.now(timezone.utc)

        # один запрос: join sessions → users
        stmt = (
            select(
                UserORM.id,
                UserORM.username,
                UserORM.email,
                UserORM.password_hash,
                UserORM.role,
                UserORM.is_active,
            )
            .select_from(
                join(UserSessionORM, UserORM, UserSessionORM.user_id == UserORM.id)
            )
            .where(
                and_(
                    UserSessionORM.id == session_id,
                    UserSessionORM.revoked_at.is_(None),
                    UserSessionORM.expires_at > now,
                )
            )
            .limit(1)
        )

        row = (await db.execute(stmt)).one_or_none()
        if not row:
            return None

        (u_id, u_username, u_email, u_hash, u_role, u_active) = row

        # Ре-гидратация доменной сущности через твои VO
        user = User.from_storage(
            id=UserId(u_id),
            username=Username(u_username),
            email=Email(u_email),
            password_hash=UserPasswordHash(u_hash),
            role=UserRole(u_role),
            is_active=bool(u_active),
        )
        return user

    async def delete_user_session_by_user_id(self, db: AsyncSession, user_id: UserId) -> None:
        await db.execute(delete(UserSessionORM).where(UserSessionORM.user_id==user_id.value))