from pydantic import BaseModel, Field

from app.domain.value_objects.constants import (
    RAW_PASSWORD_MAX_LEN,
    RAW_PASSWORD_MIN_LEN,
    USERNAME_MAX_LEN,
    USERNAME_MIN_LEN,
    EMAIL_MAX_LEN,
    EMAIL_MIN_LEN
)


class ErrorResponse(BaseModel):
    detail: str


class Token(BaseModel):
    access_token: str
    token_type: str

class LogoutResponse(BaseModel):
    detail: str


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=USERNAME_MIN_LEN, max_length=USERNAME_MAX_LEN)
    email: str = Field(..., min_length=EMAIL_MIN_LEN, max_length=EMAIL_MAX_LEN)
    password: str = Field(
        ..., min_length=RAW_PASSWORD_MIN_LEN, max_length=RAW_PASSWORD_MAX_LEN
    )
    role: str


class CreateUserResponse(BaseModel):
    id: str
    email: str = Field(..., min_length=EMAIL_MIN_LEN, max_length=EMAIL_MAX_LEN)
    role: str


class DeleteUserResponse(BaseModel):
    detail: str

class UpdateUserRequest(BaseModel):
    username: str|None = Field(default=None, min_length=USERNAME_MIN_LEN, max_length=USERNAME_MAX_LEN)
    password: str|None = Field(default=None, min_length=RAW_PASSWORD_MIN_LEN, max_length=RAW_PASSWORD_MAX_LEN)
    email: str|None = Field(default=None, min_length=EMAIL_MIN_LEN, max_length=EMAIL_MAX_LEN)
    role: str|None = None

class UpdateUserResponse(BaseModel):
    id: str
    username: str = Field(..., min_length=USERNAME_MIN_LEN, max_length=USERNAME_MAX_LEN)
    email: str = Field(..., min_length=EMAIL_MIN_LEN, max_length=EMAIL_MAX_LEN)
    role: str

class ViewOrdersResponse(BaseModel):
    detail: str

class ViewPaymentsResponse(BaseModel):
    detail: str