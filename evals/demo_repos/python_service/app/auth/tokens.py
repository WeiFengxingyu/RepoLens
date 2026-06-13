from dataclasses import dataclass
from datetime import datetime


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    expires_at: datetime
    scopes: tuple[str, ...]


def decode_token(token: str) -> TokenClaims:
    subject, expires_at = token.split(":", 1)
    return TokenClaims(subject=subject, expires_at=datetime.fromisoformat(expires_at), scopes=("user",))


def validate_access_token(token: str, now: datetime) -> TokenClaims:
    claims = decode_token(token)
    if claims.expires_at <= now:
        raise AuthError("token expired")
    if not claims.subject:
        raise AuthError("token missing subject")
    return claims
