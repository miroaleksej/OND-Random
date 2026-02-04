from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base import ProtocolObservation
from .utils import hash_to_int


@dataclass(frozen=True)
class ECDSASignature:
    r: int
    s: int


@dataclass(frozen=True)
class ECDSAParams:
    n: int
    hash_name: str = "sha256"


class ECDSAObservation(ProtocolObservation):
    """ECDSA observation mapping.

    Modes:
    - "rs": [r, s]
    - "urz": [u_r, u_z] where u_r = r * s^{-1} mod n, u_z = e * s^{-1} mod n
    - "rz": [r, e]
    - "uz": [u_z]
    """

    def __init__(self, params: ECDSAParams, mode: str = "urz"):
        self.params = params
        self.mode = mode
        if mode not in {"rs", "urz", "rz", "uz"}:
            raise ValueError("mode must be one of: rs, urz, rz, uz")

    @property
    def dimension(self) -> int:
        return 1 if self.mode == "uz" else 2

    @property
    def modulus(self) -> int | None:
        return self.params.n

    def observe(self, signature: ECDSASignature, message=None) -> np.ndarray:
        n = self.params.n
        r = int(signature.r) % n
        s = int(signature.s) % n
        if self.mode == "rs":
            return np.array([r, s], dtype=np.int64)
        if message is None:
            raise ValueError("message is required for mode: %s" % self.mode)
        e = hash_to_int(message, self.params.hash_name, n)
        if self.mode == "rz":
            return np.array([r, e], dtype=np.int64)
        inv_s = pow(s, -1, n)
        u_r = (r * inv_s) % n
        u_z = (e * inv_s) % n
        if self.mode == "uz":
            return np.array([u_z], dtype=np.int64)
        return np.array([u_r, u_z], dtype=np.int64)


def ecdsa_pair_invariant(sig_i: ECDSASignature, msg_i, sig_j: ECDSASignature, msg_j, params: ECDSAParams) -> int:
    """Compute OND pair invariant D_ij = r_j e_i - r_i e_j (mod n)."""
    n = params.n
    e_i = hash_to_int(msg_i, params.hash_name, n)
    e_j = hash_to_int(msg_j, params.hash_name, n)
    return (sig_j.r * e_i - sig_i.r * e_j) % n
