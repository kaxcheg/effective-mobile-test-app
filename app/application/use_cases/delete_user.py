from __future__ import annotations

from typing import Callable, override

from app.application.dto import DeleteUserInputDTO, DeleteUserOutputDTO
from app.application.exceptions import ConcurrencyError
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
from app.domain.value_objects import Username, UserRawPassword, UserRole, Email, UserId


class DeleteUserUseCase(AuthorizeUserUseCase[DeleteUserInputDTO, DeleteUserOutputDTO]):
    """Use case for deleting users (admin-only)."""

    logger = get_logger(__name__)

    @override
    def __init__(
        self,
        auth_service: AuthorizeService,
        user: User,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        """Initialize with dependencies."""
        super().__init__(
            auth_service=auth_service,
            user=user
        )
        self._uow_factory = uow_factory
    @override
    async def run(
        self,
        dto: DeleteUserInputDTO,
        presenter: AuthPresenter[DeleteUserOutputDTO],
    ) -> None:
        """Validate input and delete user in repository."""

        async with self._uow_factory() as uow:
            repo = uow.get_repo(UserRepository)
            user = await repo.get_by_id(UserId.from_str(dto.id))

            if user is None:
                presenter.not_found(f"User id:{dto.id} not found")
            else:
                user.deactivate()
                await repo.save(user)

                presenter.ok(
                    DeleteUserOutputDTO(f"User id:{user.id.value} was deleted.")
                )
                self.logger.info(
                    {
                        "event": "user_deleted",
                        "use_case": self.__class__.__name__,
                        "user_id": str(user.id),
                    }
                )
