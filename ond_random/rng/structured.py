from __future__ import annotations

from .base import RNG


class MaskedRNG(RNG):
    """Masks lower bits of the source RNG output (grid/comb structure)."""

    def __init__(self, source: RNG, mask_low_bits: int = 4):
        if mask_low_bits < 0 or mask_low_bits > 7:
            raise ValueError("mask_low_bits must be in [0, 7]")
        self._source = source
        self._mask_low_bits = mask_low_bits

    def random_bytes(self, n: int) -> bytes:
        data = bytearray(self._source.random_bytes(n))
        if self._mask_low_bits == 0:
            return bytes(data)
        # Apply mask per byte
        mask = (0xFF << self._mask_low_bits) & 0xFF
        for i in range(len(data)):
            data[i] &= mask & 0xFF
        return bytes(data)


class BoundedRNG(RNG):
    """Restricts output to a smaller range and rescales (phase restriction)."""

    def __init__(self, source: RNG, bound_bits: int = 12):
        if bound_bits <= 0 or bound_bits > 32:
            raise ValueError("bound_bits must be in (0, 32]")
        self._source = source
        self._bound = 1 << bound_bits

    def random_bytes(self, n: int) -> bytes:
        # Generate bytes by drawing 32-bit words and compressing to bound.
        out = bytearray()
        while len(out) < n:
            word = int.from_bytes(self._source.random_bytes(4), "big")
            value = word % self._bound
            # Rescale to full byte range by simple repetition
            out.extend(value.to_bytes(4, "big"))
        return bytes(out[:n])
