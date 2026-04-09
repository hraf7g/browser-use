from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
HASH_BYTES = 32
HASH_SCHEME = "pbkdf2_sha256"


class PasswordHashError(ValueError):
    """Raised when a password hash cannot be parsed or is invalid."""


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256.

    Output format:
        pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    """
    normalized_password = _normalize_password(password)
    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        normalized_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"{HASH_SCHEME}${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored password hash."""
    normalized_password = _normalize_password(password)
    scheme, iterations, salt, expected_hash = _parse_password_hash(password_hash)

    if scheme != HASH_SCHEME:
        raise PasswordHashError("unsupported password hash scheme")

    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        normalized_password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_hash),
    )
    return hmac.compare_digest(derived_key, expected_hash)


def _normalize_password(password: str) -> str:
    """Validate and normalize user-provided password input."""
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    if not password:
        raise ValueError("password must not be empty")

    return password


def _parse_password_hash(password_hash: str) -> tuple[str, int, bytes, bytes]:
    """Parse the stored password hash format into typed components."""
    if not isinstance(password_hash, str):
        raise TypeError("password_hash must be a string")

    parts = password_hash.split("$")
    if len(parts) != 4:
        raise PasswordHashError("invalid password hash format")

    scheme, iterations_raw, salt_b64, hash_b64 = parts

    try:
        iterations = int(iterations_raw)
    except ValueError as exc:
        raise PasswordHashError("invalid password hash iteration count") from exc

    if iterations <= 0:
        raise PasswordHashError("password hash iteration count must be positive")

    try:
        salt = base64.b64decode(salt_b64.encode("ascii"), validate=True)
        expected_hash = base64.b64decode(hash_b64.encode("ascii"), validate=True)
    except Exception as exc:
        raise PasswordHashError("invalid base64 data in password hash") from exc

    if not salt:
        raise PasswordHashError("password hash salt must not be empty")

    if not expected_hash:
        raise PasswordHashError("password hash digest must not be empty")

    return scheme, iterations, salt, expected_hash
