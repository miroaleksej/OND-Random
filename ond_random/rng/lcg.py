from __future__ import annotations

from .base import RNG


class LCGRNG(RNG):
    """Linear Congruential Generator (64-bit)."""

    def __init__(self, seed: int, a: int = 6364136223846793005, c: int = 1442695040888963407, m: int = 1 << 64):
        if m <= 0:
            raise ValueError("m must be positive")
        self._a = a % m
        self._c = c % m
        self._m = m
        self._state = seed % m

    def _next_u64(self) -> int:
        self._state = (self._a * self._state + self._c) % self._m
        return self._state

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        out = bytearray()
        while len(out) < n:
            out.extend(self._next_u64().to_bytes(8, "big"))
        return bytes(out[:n])
