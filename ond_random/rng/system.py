import os

from .base import RNG


class SystemRNG(RNG):
    """OS-provided CSPRNG (e.g., /dev/urandom)."""

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        return os.urandom(n)
