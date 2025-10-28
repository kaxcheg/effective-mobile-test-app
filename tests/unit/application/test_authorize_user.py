import pytest

from app.domain.value_objects import UserRole

from app.application.dto import CreateUserInputDTO, CreateUserOutputDTO
from app.application.ports.presenters import AuthPresenter, State
from app.application.use_cases import CreateUserUseCase

from tests.adapters import FakeAuthService, FakeCreateUserPresenter


@pytest.mark.asyncio
async def test_authorize_success(
    current_user, 
    successful_auth_service,
    uow_factory,
    password_hasher,
    id_generator):
    """Test authentication fails with wrong password."""
    
    uc = CreateUserUseCase(
        successful_auth_service, 
        current_user,
        uow_factory,
        password_hasher,
        id_generator
    )

    presenter = FakeCreateUserPresenter()
    dto = CreateUserInputDTO(
        username="",
        email="test@email.com",
        password="password123",
        role=UserRole.USER
    )
    await uc.execute(dto, presenter)
    
    assert presenter.state is not State.FORBIDDEN


@pytest.mark.asyncio
async def test_authorize_insufficient_role(
    current_user, 
    uow_factory,
    password_hasher,
    id_generator):
    """Test authorization fails when user has insufficient role."""
    
    auth_service = FakeAuthService(
        is_role_ensured=False,
    )
    
    uc = CreateUserUseCase(
            auth_service, 
            current_user,
            uow_factory,
            password_hasher,
            id_generator
        )    
    presenter = FakeCreateUserPresenter()
    dto = CreateUserInputDTO(
        username="",
        email="test@email.com",
        password="password123",
        role=UserRole.USER
    )
    
    await uc.execute(dto, presenter)
    
    assert presenter.state == State.FORBIDDEN
    assert presenter.response == "Forbidden"
