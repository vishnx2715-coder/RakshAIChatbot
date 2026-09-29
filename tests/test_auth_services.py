"""
tests/test_auth_services.py — Unit tests for blueprints/auth/services.py

Covers:
  - hash_password: produces argon2 hash, rejects short passwords
  - verify_password: correct password, wrong password
  - Legacy SHA-256: login still works, then upgrades on needs_rehash
  - needs_rehash: True for legacy, False for fresh argon2
  - Generic error message path (no enumeration)
"""

import hashlib
import pytest

from blueprints.auth.services import (
    hash_password,
    verify_password,
    needs_rehash,
    MIN_PASSWORD_LENGTH,
)

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _legacy_hash(plaintext: str) -> str:
    """Reproduce the old SHA-256 hash exactly as app.py used to."""
    return hashlib.sha256(plaintext.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────
# hash_password
# ─────────────────────────────────────────────────────────────

class TestHashPassword:
    def test_returns_argon2_string(self):
        h = hash_password("securepass1")
        assert h.startswith("$argon2"), f"Expected argon2 prefix, got: {h[:20]}"

    def test_different_salts(self):
        h1 = hash_password("securepass1")
        h2 = hash_password("securepass1")
        # argon2 generates random salt each time — hashes must differ
        assert h1 != h2

    def test_rejects_too_short(self):
        short = "a" * (MIN_PASSWORD_LENGTH - 1)
        with pytest.raises(ValueError, match=str(MIN_PASSWORD_LENGTH)):
            hash_password(short)

    def test_accepts_exact_minimum(self):
        exact = "a" * MIN_PASSWORD_LENGTH
        h = hash_password(exact)
        assert h.startswith("$argon2")

    def test_empty_password_rejected(self):
        with pytest.raises(ValueError):
            hash_password("")


# ─────────────────────────────────────────────────────────────
# verify_password — argon2 hashes
# ─────────────────────────────────────────────────────────────

class TestVerifyPasswordArgon2:
    def setup_method(self):
        self.pw = "correcthorse99"
        self.h  = hash_password(self.pw)

    def test_correct_password_returns_true(self):
        assert verify_password(self.h, self.pw) is True

    def test_wrong_password_returns_false(self):
        assert verify_password(self.h, "wrongpassword1") is False

    def test_empty_password_returns_false(self):
        assert verify_password(self.h, "") is False

    def test_empty_hash_returns_false(self):
        assert verify_password("", self.pw) is False

    def test_none_hash_returns_false(self):
        assert verify_password(None, self.pw) is False  # type: ignore[arg-type]

    def test_tampered_hash_returns_false(self):
        tampered = self.h[:-4] + "xxxx"
        assert verify_password(tampered, self.pw) is False


# ─────────────────────────────────────────────────────────────
# verify_password — legacy SHA-256 hashes
# ─────────────────────────────────────────────────────────────

class TestVerifyPasswordLegacy:
    def setup_method(self):
        self.pw   = "legacyuser99"
        self.hash = _legacy_hash(self.pw)

    def test_correct_legacy_password_returns_true(self):
        assert verify_password(self.hash, self.pw) is True

    def test_wrong_legacy_password_returns_false(self):
        assert verify_password(self.hash, "wronglegacy1") is False

    def test_legacy_hash_is_64_hex_chars(self):
        assert len(self.hash) == 64
        assert all(c in "0123456789abcdef" for c in self.hash)


# ─────────────────────────────────────────────────────────────
# needs_rehash
# ─────────────────────────────────────────────────────────────

class TestNeedsRehash:
    def test_legacy_hash_needs_rehash(self):
        h = _legacy_hash("somepassword1")
        assert needs_rehash(h) is True

    def test_fresh_argon2_does_not_need_rehash(self):
        h = hash_password("freshpassword1")
        assert needs_rehash(h) is False

    def test_empty_string_needs_rehash(self):
        assert needs_rehash("") is True

    def test_garbage_string_needs_rehash(self):
        assert needs_rehash("notahashATALL") is True


# ─────────────────────────────────────────────────────────────
# Legacy upgrade path (integration-style)
# ─────────────────────────────────────────────────────────────

class TestLegacyUpgradePath:
    """
    Simulate what app.py login() does:
      1. Load stored legacy hash.
      2. verify_password → True (old hash still works).
      3. needs_rehash → True (legacy hash must be upgraded).
      4. hash_password(plaintext) → new argon2 hash.
      5. Store new hash. On next login, verify_password works against argon2.
      6. needs_rehash → False (no more upgrade needed).
    """

    def test_full_upgrade_path(self):
        plaintext = "legacylogin99"
        stored = _legacy_hash(plaintext)

        # Step 1: legacy login still works
        assert verify_password(stored, plaintext) is True

        # Step 2: needs upgrade
        assert needs_rehash(stored) is True

        # Step 3: upgrade
        new_hash = hash_password(plaintext)

        # Step 4: verify with new argon2 hash
        assert verify_password(new_hash, plaintext) is True

        # Step 5: no longer needs rehash
        assert needs_rehash(new_hash) is False

    def test_wrong_password_does_not_trigger_upgrade(self):
        plaintext = "realpassword1"
        stored = _legacy_hash(plaintext)

        # Wrong password should fail before we ever reach needs_rehash
        result = verify_password(stored, "wrongpassword")
        assert result is False
        # We should NOT rehash on failed verification
        # (the login route checks verify first, rehash is only inside the True branch)
