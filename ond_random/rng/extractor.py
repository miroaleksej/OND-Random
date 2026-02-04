from __future__ import annotations

import hashlib
import os

from .base import RNG


class ONDMaxRNG(RNG):
    """Extractor-based RNG that amplifies and stabilizes source entropy.

    This is designed to be OND-maximal by whitening and de-correlating
    any structured source using SHAKE256 as a sponge-like extractor.
    """

    def __init__(
        self,
        source: RNG | None = None,
        seed_bytes: int = 64,
        reseed_interval: int = 1 << 20,
        personalization: bytes = b"OND-RANDOM-v1",
    ):
        if seed_bytes <= 0:
            raise ValueError("seed_bytes must be positive")
        if reseed_interval <= 0:
            raise ValueError("reseed_interval must be positive")
        self._source = source
        self._seed_bytes = seed_bytes
        self._reseed_interval = reseed_interval
        self._personalization = personalization
        self._counter = 0
        self._generated = 0
        self._key = self._seed()
        self._buffer = b""

    def _seed(self) -> bytes:
        if self._source is None:
            seed = os.urandom(self._seed_bytes)
        else:
            seed = self._source.random_bytes(self._seed_bytes)
        shake = hashlib.shake_256()
        shake.update(self._personalization)
        shake.update(seed)
        return shake.digest(64)

    def _reseed(self) -> None:
        if self._source is None:
            seed = os.urandom(self._seed_bytes)
        else:
            seed = self._source.random_bytes(self._seed_bytes)
        shake = hashlib.shake_256()
        shake.update(self._key)
        shake.update(seed)
        shake.update(self._counter.to_bytes(8, "big"))
        self._key = shake.digest(64)
        self._generated = 0

    def _next_block(self, size: int = 64) -> bytes:
        shake = hashlib.shake_256()
        shake.update(self._key)
        shake.update(self._counter.to_bytes(8, "big"))
        block = shake.digest(size)
        self._counter = (self._counter + 1) & 0xFFFFFFFFFFFFFFFF
        self._generated += size
        if self._generated >= self._reseed_interval:
            self._reseed()
        return block

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        out = bytearray()
        if self._buffer:
            take = min(n, len(self._buffer))
            out.extend(self._buffer[:take])
            self._buffer = self._buffer[take:]
            if len(out) >= n:
                return bytes(out)
        while len(out) < n:
            block = self._next_block()
            take = min(n - len(out), len(block))
            out.extend(block[:take])
            if take < len(block):
                self._buffer = block[take:]
        return bytes(out)
