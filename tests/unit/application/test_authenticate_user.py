import pytest

from app.application.dto import AuthRequestDTO, AuthResponseDTO
from app.application.ports import State
from app.application.use_cases import AuthenticateUserUseCase

from tests.adapters import TestUser, FakeAuthenticationPresenter


@pytest.mark.asyncio
async def test_successful_authentication(authenticate_use_case:AuthenticateUserUseCase, initial_users:list[TestUser]):
    """Test successful user authentication."""
    test_user = initial_users[0]
    auth_request = AuthRequestDTO(
        email=test_user.email,
        raw_password=test_user.raw_password
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.OK
    assert isinstance(presenter.response, AuthResponseDTO)
    assert presenter.response.user_id == test_user.id
    assert presenter.response.email == test_user.email
    assert presenter.response.role == test_user.role


@pytest.mark.asyncio
async def test_authentication_with_wrong_password(authenticate_use_case:AuthenticateUserUseCase, initial_users:list[TestUser]):
    """Test authentication fails with wrong password."""
    test_user = initial_users[0]
    auth_request = AuthRequestDTO(
        email=test_user.email,
        raw_password=initial_users[0].raw_password+"x"
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"


@pytest.mark.asyncio
async def test_authentication_with_nonexistent_user(authenticate_use_case:AuthenticateUserUseCase):
    """Test authentication fails with non-existent user."""

    auth_request = AuthRequestDTO(
        email="nonexistent_user@email.com",
        raw_password="any_password"
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"


@pytest.mark.asyncio
async def test_authentication_with_invalid_email_format(authenticate_use_case:AuthenticateUserUseCase):
    """Test authentication fails with invalid email format."""

    auth_request = AuthRequestDTO(
        email="",
        raw_password="testpass123"
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"


@pytest.mark.asyncio
async def test_authentication_with_invalid_password_format(authenticate_use_case:AuthenticateUserUseCase, initial_users:list[TestUser]):
    """Test authentication fails with invalid password format."""

    test_user = initial_users[0]
    auth_request = AuthRequestDTO(
        email=test_user.email,
        raw_password=""
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"


@pytest.mark.asyncio
async def test_authentication_with_wrong_email_and_password(authenticate_use_case:AuthenticateUserUseCase):
    """Test authentication fails with both wrong email and password."""

    auth_request = AuthRequestDTO(
        email="wrong_email@email.com",
        raw_password="wrong_password"
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"


@pytest.mark.asyncio
async def test_authentication_with_case_sensitive_email(authenticate_use_case:AuthenticateUserUseCase, initial_users:list[TestUser]):
    """Test that email is case-sensitive."""

    test_user = initial_users[0]
    auth_request = AuthRequestDTO(
        email=test_user.email.upper(),
        raw_password=test_user.raw_password
    )
    presenter = FakeAuthenticationPresenter()
    
    await authenticate_use_case.execute(auth_request, presenter)
    
    assert presenter.state == State.UNAUTHORIZED
    assert presenter.response == "Invalid credentials"