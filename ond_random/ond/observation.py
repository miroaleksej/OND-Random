from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..rng.base import RNG


@dataclass(frozen=True)
class ObservationMap:
    dimension: int = 4
    word_bits: int = 32
    stride: int = 1

    @property
    def word_bytes(self) -> int:
        if self.word_bits % 8 != 0:
            raise ValueError("word_bits must be a multiple of 8")
        return self.word_bits // 8

    @property
    def modulus(self) -> int:
        return 1 << self.word_bits

    def _dtype(self) -> str:
        return {1: ">u1", 2: ">u2", 4: ">u4", 8: ">u8"}[self.word_bytes]

    def from_bytes(self, data: bytes) -> np.ndarray:
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
        if self.stride <= 0:
            raise ValueError("stride must be positive")
        if self.word_bits not in (8, 16, 32, 64):
            raise ValueError("word_bits must be 8, 16, 32, or 64")
        total_words = len(data) // self.word_bytes
        if total_words < self.dimension:
            return np.empty((0, self.dimension), dtype=np.uint64)
        trimmed = data[: total_words * self.word_bytes]
        arr = np.frombuffer(trimmed, dtype=self._dtype()).astype(np.uint64)
        if self.stride == self.dimension:
            count = arr.size // self.dimension
            arr = arr[: count * self.dimension]
            return arr.reshape(count, self.dimension)
        # Sliding window with stride
        max_start = arr.size - self.dimension
        indices = range(0, max_start + 1, self.stride)
        windows = [arr[i : i + self.dimension] for i in indices]
        return np.array(windows, dtype=np.uint64)

    def from_rng(self, rng: RNG, samples: int) -> np.ndarray:
        if samples <= 0:
            raise ValueError("samples must be positive")
        total_words = samples * self.stride + (self.dimension - self.stride)
        data = rng.random_bytes(total_words * self.word_bytes)
        return self.from_bytes(data)


# Normalization intentionally omitted: OND metrics operate on raw observations.
