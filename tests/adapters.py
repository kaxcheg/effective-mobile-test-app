from typing import TypeVar, Callable, ClassVar
from dataclasses import dataclass, asdict

from app.domain.entities.user import User
from app.domain.entities.user.repo import Repository, UserRepository
from app.domain.value_objects import UserId, UserPasswordHash, UserRawPassword, UserRole, Username, Email

from app.domain.value_objects.constants import HASH_LEN
from app.application.dto.base import DTO
from app.application.dto import AuthResponseDTO, CreateUserOutputDTO, CredentialDTO
from app.application.ports.presenters import Presenter, AuthPresenter
from app.application.ports.uow import UnitOfWork
from app.application.ports import AuthorizeService, PasswordVerifier, PasswordHasher, UserIdGenerator
from app.application.exceptions import IntegrityUserError, NotAuthenticatedError, NotAuthorizedError

@dataclass
class TestUser:
    """Test user data structure."""
    id: str
    username: str
    email: str
    raw_password: str
    password_hash: str
    role: str

class FakePasswordVerifier(PasswordVerifier):
    """Fake password verifier that compares hash with raw for testing."""
    
    def __init__(self, initial_users: list[TestUser]) -> None:
        self.hash_to_raw = {}
        self.hash_to_raw = {
            UserPasswordHash(user.password_hash.encode()): UserRawPassword(user.raw_password) 
            for user in initial_users
        }
    
    def verify(self, raw_password: UserRawPassword, hashed_password: UserPasswordHash) -> bool:
        """Verify password by comparing with known hash-to-raw mapping."""
        expected_raw = self.hash_to_raw.get(hashed_password)
        return expected_raw == raw_password if expected_raw else False


class FakeAuthenticationPresenter(Presenter[AuthResponseDTO]):
    """Test presenter implementation."""

class FakeAuthorizationPresenter(AuthPresenter[DTO]):
    """Test presenter implementation."""    

class FakeCreateUserPresenter(AuthPresenter[CreateUserOutputDTO]):
    """Test Auth presenter implementation."""


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""
    
    def __init__(self, initial_users:list[TestUser]) -> None:
        self.users_by_id:dict[UserId,User] = {}
        self.users_by_email:dict[Email,User] = {}

        for user in initial_users:
            user_instance = User.from_storage(
                id=UserId.from_str(user.id),
                email=Email(user.email),
                username=Username(user.username),
                password_hash=UserPasswordHash(user.password_hash.encode()),
                role=UserRole(user.role)
            )
            self.users_by_id[UserId.from_str(user.id)] = user_instance
            self.users_by_email[Email(user.email)] = user_instance
    
    async def get_by_id(self, user_id: UserId) -> User | None:
        """Get user by ID."""
        return self.users_by_id.get(user_id)
    
    async def get_by_email(self, email: Email) -> User | None:
        """Get user by email."""
        return self.users_by_email.get(email)

    async def add(self, user: User) -> None:
        """Save or update user."""
        if user.id in self.users_by_id or user.email in self.users_by_email:
            raise IntegrityUserError
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        
        
R = TypeVar("R", bound=Repository)
type RepoFactory[R: Repository] = Callable


class FakeUoW(UnitOfWork):
    """Unit-of-Work adapter for SQLite testing."""

    _REGISTRY: ClassVar[dict[type[Repository], RepoFactory]] = {
        UserRepository: InMemoryUserRepository,
    }

    def __init__(self, initial_users: list[TestUser]):
        self.initial_users = initial_users

    async def _open(self) -> None:
        """Begin a new transactional session."""
        pass

    async def commit(self) -> None:
        """Commit active transaction."""
        pass

    async def rollback(self) -> None:
        """Rollback active transaction."""
        pass

    async def _close(self) -> None:
        """Close session safely."""
        pass

    def get_repo(self, iface: type[R]) -> R:
        repo_class = self._REGISTRY[iface]
        repo = repo_class(self.initial_users)
        from typing import cast
        return cast(R, repo)


class FakeAuthService(AuthorizeService):
    """Test authentication service implementation."""
    
    def __init__(self, is_role_ensured: bool):
        self.is_role_ensured = is_role_ensured
        # self.is_user_found = is_user_found
        
    def ensure_role(self, user_id: UserId, user_role: UserRole, required_roles: list[UserRole]) -> None:
        """Check if user has required role."""
        if not self.is_role_ensured:
            raise NotAuthorizedError(f"User role {user_role} does not match target roles {required_roles}")

class FakePasswordHasher(PasswordHasher):
    """Test password hasher implementation."""
    
    def __init__(self, hash_prefix: str = "hashed_"):
        self.hash_prefix = hash_prefix
        
    def hash(self, raw_password: UserRawPassword) -> UserPasswordHash:
        """Create a fake hash from raw password."""

        fake_hash = (self.hash_prefix + raw_password.value)[:HASH_LEN]
        fake_hash = fake_hash.ljust(HASH_LEN, 'x')
        return UserPasswordHash(fake_hash.encode())
    
class FakeIdGenerator(UserIdGenerator):
    """Test ID generator implementation."""
    
    def new(self) -> UserId:
        """Generate new unique ID."""
        return UserId.new()


