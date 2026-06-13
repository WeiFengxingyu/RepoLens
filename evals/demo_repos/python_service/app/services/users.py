from app.auth.tokens import TokenClaims
from app.repositories.users import UserRepository


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    def load_current_user(self, claims: TokenClaims) -> dict[str, str]:
        return self.repository.get_user(claims.subject)
