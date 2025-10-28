from __future__ import annotations

import traceback
from typing import Awaitable, Callable, Final

from uuid import UUID

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.config.logging import get_logger
from app.interface.http.routes import auth, users, orders, payments
from app.interface.http.auth.ports import TokenService, AuthenticateService
from app.infrastructure.security.jwt_service import JwtTokenExpired, JwtTokenInvalid
from app.infrastructure.db.sqlalchemy.setup import get_session_factory
from app.domain.value_objects import UserId
from app.interface.http.routes.dependencies import jwt_service
from app.interface.http.routes.dependencies import auth_session_service

logger = get_logger(__name__)  # Reuse module-level logger.


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""

    app = FastAPI(title="effective-mobile-test-app")
    app.include_router(users.router, tags=["User"])
    app.include_router(auth.router, tags=["Auth"])
    app.include_router(orders.router, tags=["Orders"])
    app.include_router(payments.router, tags=["Payments"])
    return app


app = create_app()


def custom_openapi():
    """
    Заменяем requestBody для /auth/login, чтобы в Swagger показывались только email и password.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Custom Login API",
        version="1.0.0",
        description="Auth endpoint with email & password only",
        routes=app.routes,
    )

    path = "/auth/login"
    method = "post"
    if path in openapi_schema["paths"]:
        request_body = {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "example": "user@example.com"},
                            "password": {"type": "string", "example": "secret"},
                        },
                        "required": ["email", "password"],
                    }
                }
            },
        }
        openapi_schema["paths"][path][method]["requestBody"] = request_body

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.get("/health", tags=["Health"])
def healthcheck() -> dict[str, str]:
    """Return simple health status."""
    return {"status": "ok"}


PUBLIC_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/health", "/auth/login")

@app.middleware("http")
async def catch_unhandled_exceptions_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Convert unexpected exceptions to a 500 JSON error and log the trace."""
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            {
                "event": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

@app.middleware("http")
async def auth_middleware(
    request: Request,
    call_next,
    _jwt: TokenService = jwt_service,
    _auth: AuthenticateService = auth_session_service,
    _session_factory: async_sessionmaker[AsyncSession] = get_session_factory(),
):
    if request.method == "OPTIONS" or any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES):
        return await call_next(request)

    # Bearer токен
    auth_hdr = request.headers.get("Authorization", "")
    if not auth_hdr.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})
    token = auth_hdr[len("Bearer "):].strip()

    # Декод и базовая валидация
    try:
        claims = _jwt.decode(token, verify_exp=True)
    except JwtTokenExpired:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})
    except JwtTokenInvalid:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})

    sub = claims.get("sub")
    sid_str = claims.get("sid")
    if not sub or not sid_str:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})

    # Cookie vs token sid
    cookie_sid = request.cookies.get("session_id")
    if not cookie_sid or cookie_sid != sid_str:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})

    # Работаем с БД ТУТ: без генераторов, только sessionmaker
    async with _session_factory() as db:
        async with db.begin():
            user = await _auth.get_user_by_session_id(db, UUID(sid_str))
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})

    # sub == user.id (VO)
    try:
        sub_vo = UserId.from_str(sub)
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})
    if sub_vo != user.id:
        return JSONResponse(status_code=401, content={"detail": "Not authorized."})

    request.state.user = user
    return await call_next(request)



