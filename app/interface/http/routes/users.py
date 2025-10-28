from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.value_objects import UserId
from app.application.dto import CreateUserInputDTO, CreateUserOutputDTO, DeleteUserInputDTO, DeleteUserOutputDTO, UpdateUserInputDTO, UpdateUserOutputDTO
from app.interface.http.auth.ports import AuthenticateService
from app.application.ports.presenters import State
from app.application.use_cases.create_user import CreateUserUseCase
from app.application.use_cases.delete_user import DeleteUserUseCase
from app.application.use_cases.update_user import UpdateUserUseCase
from app.interface.http.adapters.presenters import FastAPIAuthPresenter
from app.interface.http.routes.dependencies import get_create_user_uc, get_delete_user_uc, get_update_user_uc, get_authnticate_service, get_session_factory
from app.interface.http.schemas import (
    CreateUserRequest,
    CreateUserResponse,
    ErrorResponse,
    DeleteUserResponse,
    UpdateUserRequest,
    UpdateUserResponse
)
from app.interface.http.utils import raise_for_presenter_400_state

router = APIRouter()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateUserResponse,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        409: {"description": "Conflict", "model": ErrorResponse},
        422: {"description": "Unprocessable entity", "model": ErrorResponse},
    },
)
async def create_user(
    body: CreateUserRequest,
    uc: Annotated[CreateUserUseCase, Depends(get_create_user_uc)],
) -> CreateUserResponse:
    """Create a new user and return its public data."""
    presenter = FastAPIAuthPresenter[CreateUserOutputDTO]()
    await uc.execute(CreateUserInputDTO(**body.model_dump(mode="python")), presenter)

    if presenter.state is State.OK and isinstance(
        presenter.response, CreateUserOutputDTO
    ):
        return CreateUserResponse(**asdict(presenter.response))

    # Always raise for non-OK states to avoid returning None
    if isinstance(presenter.response, str):
        raise_for_presenter_400_state(presenter)
    else:
        raise ValueError("Wrong presenter response type")

@router.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not found", "model": ErrorResponse},
        409: {"description": "Conflict", "model": ErrorResponse},
    },
)
async def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    uc: Annotated[UpdateUserUseCase, Depends(get_update_user_uc)],
) -> UpdateUserResponse:
    """Create a new user and return its public data."""
    presenter = FastAPIAuthPresenter[UpdateUserOutputDTO]()
    dto = UpdateUserInputDTO(
        id=str(user_id),
        username=body.username,
        password=body.password,
        email=body.email,
        role=body.role
    )
    await uc.execute(dto, presenter)

    if presenter.state is State.OK and isinstance(
        presenter.response, UpdateUserOutputDTO
    ):
        return UpdateUserResponse(
            id=presenter.response.id,
            username=presenter.response.username,
            email=presenter.response.email,
            role=presenter.response.role
        )

    # Always raise for non-OK states to avoid returning None
    if isinstance(presenter.response, str):
        raise_for_presenter_400_state(presenter)
    else:
        raise ValueError("Wrong presenter response type")

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
        404: {"description": "Not found", "model": ErrorResponse},
    },
)
async def delete_user(
    user_id: UUID,
    uc: Annotated[DeleteUserUseCase, Depends(get_delete_user_uc)],
    auth: Annotated[AuthenticateService, Depends(get_authnticate_service)],
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],

) -> DeleteUserResponse:
    """Create a new user and return its public data."""
    presenter = FastAPIAuthPresenter[DeleteUserOutputDTO]()
    await uc.execute(DeleteUserInputDTO(str(user_id)), presenter)

    if presenter.state is State.OK and isinstance(
        presenter.response, DeleteUserOutputDTO
    ):
        async with session_factory() as db:
            async with db.begin():
                await auth.delete_user_session_by_user_id(db, UserId(user_id))
        return DeleteUserResponse(detail=presenter.response.msg)

    # Always raise for non-OK states to avoid returning None
    if isinstance(presenter.response, str):
        raise_for_presenter_400_state(presenter)
    else:
        raise ValueError("Wrong presenter response type")
