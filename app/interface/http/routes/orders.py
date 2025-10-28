from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.value_objects import UserId
from app.application.dto.base import DTO
from app.interface.http.auth.ports import AuthenticateService
from app.application.ports.presenters import State
from app.application.use_cases.create_user import CreateUserUseCase
from app.application.use_cases.delete_user import DeleteUserUseCase
from app.application.use_cases.update_user import UpdateUserUseCase
from app.application.use_cases.view_orders import ViewOrdersUseCase
from app.interface.http.adapters.presenters import FastAPIAuthPresenter
from app.interface.http.routes.dependencies import (
    get_create_user_uc, 
    get_delete_user_uc,
    get_update_user_uc, 
    get_authnticate_service, 
    get_session_factory,
    get_view_orders_uc
)
from app.interface.http.schemas import (
    CreateUserRequest,
    CreateUserResponse,
    ErrorResponse,
    DeleteUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    ViewOrdersResponse
)
from app.interface.http.utils import raise_for_presenter_400_state

router = APIRouter()


@router.get(
    "/orders",
    status_code=status.HTTP_200_OK,
    response_model=ViewOrdersResponse,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden", "model": ErrorResponse},
    },
)
async def get_orders(
    uc: Annotated[ViewOrdersUseCase, Depends(get_view_orders_uc)],
) -> ViewOrdersResponse:
    """Create a new user and return its public data."""
    presenter = FastAPIAuthPresenter[DTO]()
    await uc.execute(DTO(), presenter)

    if presenter.state is State.OK and isinstance(
        presenter.response, DTO
    ):
        return ViewOrdersResponse(detail="You are allowed to view orders.")

    # Always raise for non-OK states to avoid returning None
    if isinstance(presenter.response, str):
        raise_for_presenter_400_state(presenter)
    else:
        raise ValueError("Wrong presenter response type")

