from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.application.dto.base import DTO


@dataclass(slots=True, frozen=True)
class CreateUserInputDTO(DTO):
    username: str
    email: str
    password: str
    role: str


@dataclass(slots=True, frozen=True)
class CreateUserOutputDTO(DTO):
    id: str
    email: str
    role: str

@dataclass(slots=True, frozen=True)
class DeleteUserInputDTO(DTO):
    id: str

@dataclass(slots=True, frozen=True)
class DeleteUserOutputDTO(DTO):
    msg: str

@dataclass(slots=True, frozen=True)
class UpdateUserInputDTO(DTO):
    id: str
    username: str|None
    email: str|None
    password: str|None
    role: str|None

@dataclass(slots=True, frozen=True)
class UpdateUserOutputDTO(DTO):
    id: str
    username: str
    email: str
    role: str

@dataclass(slots=True, frozen=True)
class AuthRequestDTO(DTO):
    email: str
    raw_password: str


@dataclass(slots=True, frozen=True)
class AuthResponseDTO(DTO):
    user_id: str
    email: str
    role: str


@dataclass(slots=True, frozen=True)
class CredentialDTO(DTO):
    """Flat generic DTO for any kind of authentication artefact."""

    scheme: Literal[
        "bearer",  # Authorization: Bearer <token>
        "cookie",  # сookies
        "basic",  # Basic <base64>
        "apikey",  # X-Api-Key
    ]
    value: str | dict | list

@dataclass(slots=True, frozen=True)
class UserSessionDTO(DTO):
    "Session DTO"
    id: UUID
