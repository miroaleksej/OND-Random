from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .base import ProtocolObservation
from .utils import shake_words, vector_bytes


@dataclass(frozen=True)
class LatticeSignature:
    z: Sequence[int]
    c: int | Sequence[int] | None = None


@dataclass(frozen=True)
class LatticeParams:
    modulus: int
    dimension: int
    word_bits: int = 16
    mode: str = "z_mod_q"  # or "z_hash"


class LatticeObservation(ProtocolObservation):
    """Generic lattice-based observation mapping.

    Modes:
    - "z_mod_q": take first `dimension` entries of z mod q
    - "z_hash": hash z into `dimension` words using SHAKE256
    """

    def __init__(self, params: LatticeParams):
        self.params = params
        if params.mode not in {"z_mod_q", "z_hash"}:
            raise ValueError("mode must be one of: z_mod_q, z_hash")

    @property
    def dimension(self) -> int:
        return self.params.dimension

    @property
    def modulus(self) -> int | None:
        return self.params.modulus

    def observe(self, signature: LatticeSignature, message=None) -> np.ndarray:
        q = self.params.modulus
        d = self.params.dimension
        z = list(signature.z)
        if self.params.mode == "z_mod_q":
            if not z:
                raise ValueError("signature.z must not be empty")
            # Repeat z if shorter than d
            out = [(z[i % len(z)] % q) for i in range(d)]
            return np.array(out, dtype=np.int64)
        # z_hash
        data = vector_bytes(z)
        out = shake_words(data, count=d, word_bits=self.params.word_bits, modulus=q)
        return np.array(out, dtype=np.int64)


# Convenience presets

def dilithium_observation(dimension: int = 8, mode: str = "z_mod_q") -> LatticeObservation:
    # Dilithium uses q=8380417
    return LatticeObservation(LatticeParams(modulus=8380417, dimension=dimension, word_bits=32, mode=mode))
