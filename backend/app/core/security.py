import hashlib
import hmac
import secrets
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# Argon2id password hasher with standard secure parameters
password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash plaintext password with Argon2id."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return password_hasher.verify(hashed_password, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate cryptographically secure 256-bit URL-safe session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash session token with SHA-256 for persistent database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sign_cookie_value(token: str, secret: str) -> str:
    """Create HMAC-SHA256 signature for session cookie (token.signature)."""
    signature = hmac.new(
        secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{token}.{signature}"


def unsign_cookie_value(signed_value: str, secret: str) -> Optional[str]:
    """Verify HMAC-SHA256 signature on signed session cookie value and extract token."""
    if not signed_value or "." not in signed_value:
        return None

    token, signature = signed_value.split(".", 1)
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(signature, expected_sig):
        return token
    return None
