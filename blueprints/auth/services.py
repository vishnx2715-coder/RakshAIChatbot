"""
blueprints/auth/services.py — Password hashing for RAKSHA.

Uses argon2-cffi (PasswordHasher) for all new hashes.
Handles transparent upgrade of legacy SHA-256 hashes on login.

Legacy detection:
  SHA-256 hashes are exactly 64 lowercase hex characters with no "$" prefix.
  Argon2 hashes start with "$argon2" — unambiguous.

Security properties:
  - Constant-time comparison for both argon2 and legacy SHA-256.
  - Generic error message path: callers must return "Invalid credentials"
    for any failure — no user enumeration.
  - Minimum password length enforced server-side.
"""

import hashlib
import hmac
import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# ── Singleton PasswordHasher — reuse across requests ──────────
# Defaults: time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16
# These are the recommended argon2id defaults (RFC 9106 §4).
_ph = PasswordHasher()

# ── Constants ─────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 8
_LEGACY_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def hash_password(plaintext: str) -> str:
    """
    Hash a plaintext password using argon2id.
    Always use this for new registrations and after legacy upgrade.

    Returns the full argon2 hash string (includes salt + params).
    Raises ValueError if password is below minimum length.
    """
    if len(plaintext) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    return _ph.hash(plaintext)


def verify_password(stored_hash: str, plaintext: str) -> bool:
    """
    Verify plaintext against a stored hash (argon2 or legacy SHA-256).

    Returns True if the password matches, False otherwise.
    Does NOT raise — all exceptions are caught and return False
    to ensure callers always see a bool (never an unhandled exception
    leaking timing or implementation details).
    """
    if not stored_hash or not plaintext:
        return False

    if _is_legacy_hash(stored_hash):
        return _verify_legacy(stored_hash, plaintext)

    return _verify_argon2(stored_hash, plaintext)


def needs_rehash(stored_hash: str) -> bool:
    """
    Returns True if the stored hash should be upgraded.

    True when:
      - The hash is a legacy SHA-256 string (always upgrade).
      - The hash was produced with outdated argon2 parameters
        (argon2-cffi detects this automatically via check_needs_rehash).

    False when the hash is current argon2id with current parameters.
    """
    if _is_legacy_hash(stored_hash):
        return True
    try:
        return _ph.check_needs_rehash(stored_hash)
    except Exception:
        # If the hash is malformed or from an unknown scheme, flag for rehash.
        return True


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _is_legacy_hash(h: str) -> bool:
    """
    Detect a legacy SHA-256 hash:
      - Exactly 64 hexadecimal characters.
      - No "$argon2" prefix.
    Any argon2 hash starts with "$argon2id$" or "$argon2i$", so the
    two formats are unambiguous.
    """
    return bool(_LEGACY_SHA256_RE.match(h))


def _verify_legacy(stored_hex: str, plaintext: str) -> bool:
    """
    Constant-time comparison of a legacy SHA-256 hash.

    Uses hmac.compare_digest to prevent timing attacks.
    The plaintext is hashed with SHA-256 before comparison —
    same algorithm used in the original hash_pw().
    """
    expected = hashlib.sha256(plaintext.encode()).hexdigest()
    # Both are hex strings of equal length (64 chars) — safe for compare_digest.
    return hmac.compare_digest(expected, stored_hex)


def _verify_argon2(stored_hash: str, plaintext: str) -> bool:
    """
    Verify an argon2 hash using argon2-cffi.
    VerifyMismatchError → wrong password (False).
    Other exceptions (VerificationError, InvalidHashError) → treat as False.
    """
    try:
        _ph.verify(stored_hash, plaintext)
        return True
    except VerifyMismatchError:
        return False
    except (VerificationError, InvalidHashError):
        return False
    except Exception:
        return False
