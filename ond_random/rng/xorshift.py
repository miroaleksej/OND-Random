from __future__ import annotations

from .base import RNG


class XorShift128PlusRNG(RNG):
    """xorshift128+ RNG (not cryptographically secure)."""

    def __init__(self, seed1: int, seed2: int):
        if seed1 == 0 and seed2 == 0:
            raise ValueError("seeds must not both be zero")
        self._s0 = seed1 & ((1 << 64) - 1)
        self._s1 = seed2 & ((1 << 64) - 1)

    def _next_u64(self) -> int:
        s1 = self._s0
        s0 = self._s1
        self._s0 = s0
        s1 ^= (s1 << 23) & ((1 << 64) - 1)
        s1 ^= (s1 >> 17) & ((1 << 64) - 1)
        s1 ^= s0
        s1 ^= (s0 >> 26) & ((1 << 64) - 1)
        self._s1 = s1
        return (self._s0 + self._s1) & ((1 << 64) - 1)

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        out = bytearray()
        while len(out) < n:
            out.extend(self._next_u64().to_bytes(8, "big"))
        return bytes(out[:n])


# Alias for convenience
XorShiftRNG = XorShift128PlusRNG
