from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base import ProtocolObservation
from .utils import hash_to_int, int_to_bytes, to_bytes


@dataclass(frozen=True)
class SchnorrSignature:
    r: int
    s: int


@dataclass(frozen=True)
class SchnorrParams:
    n: int
    hash_name: str = "sha256"


class SchnorrObservation(ProtocolObservation):
    """Schnorr observation mapping.

    Modes:
    - "rs": [r, s]
    - "es": [e, s] where e = H(r || m) mod n
    """

    def __init__(self, params: SchnorrParams, mode: str = "es"):
        self.params = params
        self.mode = mode
        if mode not in {"rs", "es"}:
            raise ValueError("mode must be one of: rs, es")

    @property
    def dimension(self) -> int:
        return 2

    @property
    def modulus(self) -> int | None:
        return self.params.n

    def observe(self, signature: SchnorrSignature, message=None) -> np.ndarray:
        n = self.params.n
        r = int(signature.r) % n
        s = int(signature.s) % n
        if self.mode == "rs":
            return np.array([r, s], dtype=np.int64)
        if message is None:
            raise ValueError("message is required for mode: es")
        size = max(1, (n.bit_length() + 7) // 8)
        data = int_to_bytes(r, size) + to_bytes(message)
        e = hash_to_int(data, self.params.hash_name, n)
        return np.array([e, s], dtype=np.int64)
