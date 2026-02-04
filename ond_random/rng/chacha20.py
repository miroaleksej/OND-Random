from __future__ import annotations

import hashlib

from .base import RNG


def _rotl32(x: int, n: int) -> int:
    return ((x << n) & 0xFFFFFFFF) | (x >> (32 - n))


def _quarter_round(state: list[int], a: int, b: int, c: int, d: int) -> None:
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = _rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = _rotl32(state[b], 7)


def _chacha20_block(key_words: list[int], counter: int, nonce_words: list[int]) -> bytes:
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    state = constants + key_words + [counter] + nonce_words
    working = state.copy()

    for _ in range(10):
        _quarter_round(working, 0, 4, 8, 12)
        _quarter_round(working, 1, 5, 9, 13)
        _quarter_round(working, 2, 6, 10, 14)
        _quarter_round(working, 3, 7, 11, 15)

        _quarter_round(working, 0, 5, 10, 15)
        _quarter_round(working, 1, 6, 11, 12)
        _quarter_round(working, 2, 7, 8, 13)
        _quarter_round(working, 3, 4, 9, 14)

    out = [(working[i] + state[i]) & 0xFFFFFFFF for i in range(16)]
    return b"".join(word.to_bytes(4, "little") for word in out)


class ChaCha20RNG(RNG):
    """ChaCha20 RNG with 32-byte key and 12-byte nonce."""

    def __init__(self, key: bytes, nonce: bytes | None = None, counter: int = 1):
        if len(key) != 32:
            raise ValueError("key must be 32 bytes")
        if nonce is None:
            nonce = b"\x00" * 12
        if len(nonce) != 12:
            raise ValueError("nonce must be 12 bytes")
        if counter < 0 or counter > 0xFFFFFFFF:
            raise ValueError("counter out of range")
        self._key_words = [int.from_bytes(key[i:i + 4], "little") for i in range(0, 32, 4)]
        self._nonce_words = [int.from_bytes(nonce[i:i + 4], "little") for i in range(0, 12, 4)]
        self._counter = counter
        self._buffer = b""

    @classmethod
    def from_seed(cls, seed: bytes) -> "ChaCha20RNG":
        if not seed:
            raise ValueError("seed must be non-empty")
        digest = hashlib.sha512(seed).digest()
        key = digest[:32]
        nonce = digest[32:44]
        return cls(key=key, nonce=nonce, counter=1)

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
            block = _chacha20_block(self._key_words, self._counter, self._nonce_words)
            self._counter = (self._counter + 1) & 0xFFFFFFFF
            take = min(n - len(out), len(block))
            out.extend(block[:take])
            if take < len(block):
                self._buffer = block[take:]
        return bytes(out)
