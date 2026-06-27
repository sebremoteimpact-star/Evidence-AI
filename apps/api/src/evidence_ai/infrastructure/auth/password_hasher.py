"""Password hashing con Argon2id (estándar OWASP 2025+)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class Argon2PasswordHasher:
    """Argon2id con parámetros recomendados por OWASP."""

    def __init__(self) -> None:
        # OWASP 2024+: 2 iteraciones, 19 MiB memoria, 1 hilo
        self._ph = PasswordHasher(
            time_cost=2,
            memory_cost=19_456,
            parallelism=1,
            hash_len=32,
            salt_len=16,
        )

    def hash(self, password: str) -> str:
        return self._ph.hash(password)

    def verify(self, hash_: str, password: str) -> bool:
        try:
            self._ph.verify(hash_, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    def needs_rehash(self, hash_: str) -> bool:
        return self._ph.check_needs_rehash(hash_)
