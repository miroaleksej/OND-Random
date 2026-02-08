from __future__ import annotations

import hashlib
import os
from typing import Iterable, List

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


def _bytes_to_bits(data: bytes) -> List[int]:
    bits: List[int] = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_to_bytes(bits: Iterable[int]) -> bytes:
    out = bytearray()
    acc = 0
    count = 0
    for bit in bits:
        acc = (acc << 1) | (1 if bit else 0)
        count += 1
        if count == 8:
            out.append(acc)
            acc = 0
            count = 0
    if count:
        acc = acc << (8 - count)
        out.append(acc)
    return bytes(out)


def toeplitz_hash(input_bytes: bytes, seed: bytes, output_bits: int) -> bytes:
    if output_bits <= 0:
        raise ValueError("output_bits must be positive")
    input_bits = _bytes_to_bits(input_bytes)
    n = len(input_bits)
    m = output_bits
    required = n + m - 1
    seed_bits = _bytes_to_bits(seed)
    if len(seed_bits) < required:
        raise ValueError("seed is too short for requested dimensions")
    tprime = seed_bits[:required]

    out_bits: List[int] = []
    for i in range(m):
        start = (m - 1) - i
        acc = 0
        for j in range(n):
            acc ^= input_bits[j] & tprime[start + j]
        out_bits.append(acc)
    return _bits_to_bytes(out_bits)


class ToeplitzExtractorRNG(RNG):
    """Toeplitz (universal hashing) extractor.

    Generates output blocks by hashing fresh source bytes using a fixed
    Toeplitz matrix defined by `seed`. This is an information-theoretic
    extractor when the input has sufficient min-entropy.
    """

    def __init__(
        self,
        source: RNG | None = None,
        *,
        input_bytes: int = 64,
        output_bytes: int = 32,
        seed: bytes | None = None,
    ):
        if input_bytes <= 0:
            raise ValueError("input_bytes must be positive")
        if output_bytes <= 0:
            raise ValueError("output_bytes must be positive")
        self._source = source
        self._input_bytes = input_bytes
        self._output_bytes = output_bytes
        input_bits = input_bytes * 8
        output_bits = output_bytes * 8
        required_bits = input_bits + output_bits - 1
        required_bytes = (required_bits + 7) // 8
        if seed is None:
            seed = self._get_entropy(required_bytes)
        if len(seed) * 8 < required_bits:
            raise ValueError("seed is too short for requested dimensions")
        self._seed = seed[:required_bytes]

    def _get_entropy(self, n: int) -> bytes:
        if self._source is None:
            return os.urandom(n)
        return self._source.random_bytes(n)

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        out = bytearray()
        while len(out) < n:
            chunk = self._get_entropy(self._input_bytes)
            block = toeplitz_hash(chunk, self._seed, self._output_bytes * 8)
            take = min(n - len(out), len(block))
            out.extend(block[:take])
        return bytes(out)
