from __future__ import annotations

from abc import ABC
from logging import Logger
from typing import Callable, final, Any, cast

from app.application.dto.base import DTO
from app.application.exceptions import NotAuthenticatedError, NotAuthorizedError, NotFoundUserSessionError
from app.application.ports import AuthPresenter, UnitOfWork
from app.application.ports.presenters import Presenter
from app.application.ports.services import AuthorizeService
from app.config.logging import get_logger
from app.domain.entities.user import User
from app.domain.entities.user.repo import UserRepository
from app.domain.exceptions.base import DomainError
from app.domain.value_objects import UserRole

ROLE_POLICIES: dict[str, list[UserRole]] = {
    "CreateUserUseCase": [UserRole.ADMIN],
    "DeleteUserUseCase": [UserRole.ADMIN],
    "UpdateUserUseCase": [UserRole.ADMIN, UserRole.NANAGER],
    "ViewOrdersUseCase": [UserRole.ADMIN, UserRole.NANAGER, UserRole.USER],
    "ViewPaymentsUseCase": [UserRole.ADMIN, UserRole.NANAGER],
}

class UseCase[I: DTO, O: DTO](ABC):
    """Application use case contract."""

    async def execute(self, dto: I, presenter: Presenter[O]) -> None: ...


class AuthorizeUserUseCase[I: DTO, O: DTO](ABC):
    """Use case base that checks authentication and role before execution."""

    _auth: AuthorizeService

    logger: Logger = get_logger(__name__)

    def __init__(
        self,
        auth_service: AuthorizeService,
        user: User
    ) -> None:
        """Initialize with UoW factory, auth service and target role."""
        self._auth = auth_service
        self._user = user
        self._required_roles: list[UserRole] | None = ROLE_POLICIES.get(self.__class__.__name__)

    @final
    async def execute(self, dto: I, presenter: AuthPresenter[O]) -> None:
    
        try:
            assert self._required_roles is not None
            self._auth.ensure_role(self._user.id, self._user.role, self._required_roles)
        except NotAuthorizedError:
            presenter.forbidden("Forbidden")
            self.logger.warning(
                {
                    "event": "access_denied",
                    "reason": "Insufficient role permissions",
                    "use_case": f"{self.__class__.__name__}",
                    "user_id": f"{self._user.id}",
                }
            )
            return

        await self.run(dto, presenter)

    async def run(self, dto: I, presenter: AuthPresenter[O]) -> None:
        """Execute domain logic after successful authorization."""
