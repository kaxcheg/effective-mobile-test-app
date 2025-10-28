from __future__ import annotations

from typing import Callable, override
from dataclasses import fields

from app.application.dto import UpdateUserInputDTO, UpdateUserOutputDTO
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
from app.domain.value_objects import Username, UserRawPassword, UserRole, Email, UserId, UserPasswordHash


class UpdateUserUseCase(AuthorizeUserUseCase[UpdateUserInputDTO, UpdateUserOutputDTO]):
    """Use case for update users (admin-only)."""

    logger = get_logger(__name__)

    @override
    def __init__(
        self,
        auth_service: AuthorizeService,
        user: User,
        uow_factory: Callable[[], UnitOfWork],
        hasher: PasswordHasher,
    ) -> None:
        """Initialize with dependencies."""
        super().__init__(
            auth_service=auth_service,
            user=user
        )
        self._uow_factory = uow_factory
        self._hasher = hasher

    @override
    async def run(
        self,
        dto: UpdateUserInputDTO,
        presenter: AuthPresenter[UpdateUserOutputDTO],
    ) -> None:
        """Validate input and delete user in repository."""

        fields_to_update = {}
        for f in fields(dto):
            if f.name == "id":
                continue
            value = getattr(dto, f.name)
            if value is not None:
                fields_to_update[f.name] = value
                
        if not fields_to_update:
            presenter.bad_response("Bad response.")

        async with self._uow_factory() as uow:
            repo = uow.get_repo(UserRepository)
            user = await repo.get_by_id(UserId.from_str(dto.id))

            if user is None:
                presenter.not_found(f"User id:{dto.id} not found")
            else:
                try:
                    for f in fields_to_update:
                        try:
                            match f:
                                case "username":
                                    user.change_username(Username(dto.username))
                                case "email":
                                    user.change_email(Email(dto.email))
                                case "password":
                                    pwd_hash = self._hasher.hash(UserRawPassword(dto.password))
                                    user.change_password(pwd_hash)
                                case "role":
                                    user.change_role(UserRole(dto.role))
                                case _:
                                    raise ValueError("Not expected key in DTO.")
                        except (DomainError, ValueObjectError, ValueError):
                            presenter.error("Can`t update user with given atributes.")
                            return
                    updated_user = await repo.save(user)
                except IntegrityUserError:
                    presenter.conflict("User with given unique atributes already exists")
                    return

                presenter.ok(
                    UpdateUserOutputDTO(
                        id=str(updated_user.id.value),
                        username=updated_user.username.value,
                        email=updated_user.email.value,
                        role=updated_user.role
                    )
                )
                self.logger.info(
                    {
                        "event": "user_updated",
                        "use_case": self.__class__.__name__,
                        "user_id": str(user.id),
                        "username": user.username.value,
                        "email": user.email.value,
                        "role": user.role
                    }
                )
