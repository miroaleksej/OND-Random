from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class RNG(ABC):
    """Abstract RNG interface for OND Random."""

    @abstractmethod
    def random_bytes(self, n: int) -> bytes:
        raise NotImplementedError

    def random_uint64(self) -> int:
        return int.from_bytes(self.random_bytes(8), byteorder="big", signed=False)

    def random_bits(self, nbits: int) -> bytes:
        """Return a big-endian bitstring of exact length nbits."""
        if nbits <= 0:
            raise ValueError("nbits must be positive")
        nbytes = (nbits + 7) // 8
        data = bytearray(self.random_bytes(nbytes))
        excess = nbytes * 8 - nbits
        if excess:
            mask = (1 << (8 - excess)) - 1
            data[0] &= mask
        return bytes(data)

    def random_int_bits(self, nbits: int) -> int:
        """Return a non-negative integer with at most nbits."""
        return int.from_bytes(self.random_bits(nbits), byteorder="big", signed=False)

    def random_uint(self, modulus: int) -> int:
        """Uniform integer in [0, modulus) using rejection sampling."""
        if modulus <= 0:
            raise ValueError("modulus must be positive")
        # Small modulus optimization
        if modulus == 1:
            return 0
        bits = modulus.bit_length()
        bytes_len = (bits + 7) // 8
        max_val = 1 << (bytes_len * 8)
        limit = (max_val // modulus) * modulus
        while True:
            candidate = int.from_bytes(self.random_bytes(bytes_len), "big", signed=False)
            if candidate < limit:
                return candidate % modulus

    def random_vector(self, length: int, modulus: int) -> list[int]:
        if length <= 0:
            raise ValueError("length must be positive")
        return [self.random_uint(modulus) for _ in range(length)]

    def random_bytes_stream(self, chunk: int = 4096) -> Iterable[bytes]:
        """Infinite stream of random bytes in chunks."""
        if chunk <= 0:
            raise ValueError("chunk must be positive")
        while True:
            yield self.random_bytes(chunk)
