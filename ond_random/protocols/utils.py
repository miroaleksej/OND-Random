from __future__ import annotations

import hashlib
from typing import Iterable


def to_bytes(data: bytes | str) -> bytes:
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def hash_to_int(message: bytes | str | int, hash_name: str, modulus: int | None) -> int:
    if isinstance(message, int):
        if modulus is None:
            return message
        return message % modulus
    msg = to_bytes(message)
    h = hashlib.new(hash_name)
    h.update(msg)
    val = int.from_bytes(h.digest(), "big")
    if modulus is not None:
        return val % modulus
    return val


def int_to_bytes(value: int, length: int) -> bytes:
    if length <= 0:
        length = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(length, "big", signed=False)


def shake_words(data: bytes, count: int, word_bits: int, modulus: int | None) -> list[int]:
    if count <= 0:
        return []
    if word_bits <= 0 or word_bits % 8 != 0:
        raise ValueError("word_bits must be positive and multiple of 8")
    word_bytes = word_bits // 8
    shake = hashlib.shake_256()
    shake.update(data)
    buf = shake.digest(count * word_bytes)
    out = []
    for i in range(count):
        chunk = buf[i * word_bytes : (i + 1) * word_bytes]
        val = int.from_bytes(chunk, "big", signed=False)
        if modulus is not None:
            val %= modulus
        out.append(val)
    return out


def vector_bytes(values: Iterable[int], word_bytes: int = 8) -> bytes:
    out = bytearray()
    for v in values:
        out.extend(int(v).to_bytes(word_bytes, "big", signed=False))
    return bytes(out)
