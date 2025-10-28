from __future__ import annotations

from typing import TypeVar

from app.application.dto.base import DTO
from app.application.dto import AuthResponseDTO, CreateUserOutputDTO
from app.application.ports import AuthPresenter
from app.application.ports.presenters import Presenter

D = TypeVar("D", bound=DTO)

class FastAPIAuthPresenter[D: DTO](AuthPresenter[D]):
    """Presenter for create-user responses."""


class FastAPIPresenter[D: DTO](Presenter[D]):
    """Presenter for authentication responses."""
