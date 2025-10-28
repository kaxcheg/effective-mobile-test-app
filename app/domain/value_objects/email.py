from __future__ import annotations

import re

from dataclasses import dataclass
from typing import override

from app.domain.exceptions import ValueObjectError
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.constants import EMAIL_MAX_LEN, EMAIL_MIN_LEN

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$")

def validate_email_value(email_value: str) -> None:
    if not EMAIL_MIN_LEN <= len(email_value) <= EMAIL_MAX_LEN:
        raise ValueObjectError(
            f"Email must be between {EMAIL_MIN_LEN} and {EMAIL_MAX_LEN} characters."
        )
    if not EMAIL_REGEX.match(email_value):
                raise ValueObjectError(f"Invalid email format: {email_value}")

@dataclass(frozen=True, repr=False)
class Email(ValueObject):
    """email value object.

    Args:
        value: Raw email string.

    Raises:
        ValueObjectError: If length is out of bounds.
    """

    value: str

    @override
    def __post_init__(self) -> None:
        """Validate value length."""
        super().__post_init__()
        validate_email_value(self.value)

    @override
    def __str__(self) -> str:
        """Return email string.

        Returns:
            str: email.
        """
        return str(self.value)
