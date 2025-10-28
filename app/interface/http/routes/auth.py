from typing import Annotated
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response, Security, Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from app.application.dto import AuthRequestDTO, AuthResponseDTO
from app.application.ports.presenters import State
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.config.logging import get_logger
from app.domain.entities.user import User
from app.infrastructure.security.jwt_service import JwtTokenService
from app.infrastructure.db.sqlalchemy.models.user_session import UserSessionORM
from app.interface.http.adapters.presenters import FastAPIPresenter
from app.interface.http.auth.ports import AuthenticateService
from app.interface.http.routes.dependencies import (
    get_authenticate_user_uc,
    get_authnticate_service,
    get_jwt_service,
    get_session_factory, 
    security
)
from app.interface.http.schemas import ErrorResponse, LogoutResponse, Token
from app.interface.http.utils import raise_for_presenter_400_state

router = APIRouter()
logger = get_logger(__name__)


class EmailPasswordForm:
    def __init__(
        self,
        email: str = Form(..., description="Email"),
        password: str = Form(..., description="Password"),
    ):
        self.email = email
        self.password = password


@router.post(
    "/auth/login",
    status_code=200,
    response_model=Token,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        422: {"description": "Unprocessable entity", "model": ErrorResponse},
    },
)
async def login(
    form: Annotated[EmailPasswordForm, Depends(EmailPasswordForm)],
    uc: Annotated[AuthenticateUserUseCase, Depends(get_authenticate_user_uc)],
    token_service: Annotated[JwtTokenService, Depends(get_jwt_service)],
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    response: Response
) -> Token:
    """Authenticate user and return a JWT access token.

    Args:
        form: email/password form.
        uc: AuthenticateUser use case instance.
        token_service: JWT service for token issuing.

    Returns:
        Token: Bearer access token on success.
    """
    presenter = FastAPIPresenter[AuthResponseDTO]()
    dto = AuthRequestDTO(email=form.email, raw_password=form.password)
    await uc.execute(dto, presenter)
    
    if presenter.state is State.OK and isinstance(presenter.response, AuthResponseDTO):
        user_session = UserSessionORM(
            id=uuid4(),
            user_id=presenter.response.user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        async with session_factory() as db:
            async with db.begin():
                db.add(user_session)
                await db.flush()

        token = token_service.issue(
            claims={"sub": presenter.response.user_id, "role": presenter.response.role, "sid": str(user_session.id)}
        )
        logger.info(
            {"event": "token_created", "user_id": f"{presenter.response.user_id}"}
        )
        response.set_cookie(
            key="session_id",
            value=str(user_session.id),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,
        )
        return Token(access_token=token, token_type="Bearer")

    # Always raise on non-OK states
    if isinstance(presenter.response, str):
        raise_for_presenter_400_state(presenter)
    else:
        raise ValueError("Wrong presenter response type")


@router.post(
    "/auth/logout",
    status_code=200,
    response_model=LogoutResponse,
    responses={
        401: {"description": "Unauthorized", "model": ErrorResponse},
        422: {"description": "Unprocessable entity", "model": ErrorResponse},
    },
)
async def logout(
    request: Request,
    auth: Annotated[AuthenticateService, Depends(get_authnticate_service)],
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
) -> LogoutResponse:

    user: User = request.state.user
    async with session_factory() as db:
        async with db.begin():
            await auth.delete_user_session_by_user_id(db, user.id)
    return LogoutResponse(detail="Logout successfully.")

