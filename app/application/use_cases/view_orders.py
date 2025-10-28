from __future__ import annotations

from typing import Callable, override


from app.application.dto.base import DTO 
from app.application.exceptions import IntegrityUserError
from app.application.ports.presenters import AuthPresenter
from app.application.ports.services import AuthorizeService, PasswordHasher
from app.application.ports.uow import UnitOfWork
from app.application.use_cases.base import AuthorizeUserUseCase
from app.config.logging import get_logger
from app.domain.entities.user.repo import UserRepository
from app.domain.entities.user.user import User
from app.domain.exceptions import ValueObjectError
from app.domain.exceptions.base import DomainError
from app.domain.services.services import UserIdGenerator
from app.domain.value_objects import Username, UserRawPassword, UserRole, Email


class ViewOrdersUseCase(AuthorizeUserUseCase[DTO, DTO]):
    @override
    def __init__(
        self,
        auth_service: AuthorizeService,
        user: User,
    ) -> None:
        super().__init__(
            auth_service=auth_service,
            user=user
        )
    @override
    async def run(
        self,
        dto: DTO,
        presenter: AuthPresenter[DTO],
    ) -> None:
        presenter.ok(dto)
