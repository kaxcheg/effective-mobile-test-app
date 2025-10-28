from __future__ import annotations

from typing import Protocol

from app.domain.value_objects import UserId


class UserIdGenerator(Protocol):
    """Strategy interface for generating unique UserId values."""

    def new(self) -> UserId: ...
