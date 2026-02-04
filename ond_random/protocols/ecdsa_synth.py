from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .ecdsa import ECDSASignature
from .utils import vector_bytes
from ..rng.base import RNG


@dataclass(frozen=True)
class CurveParams:
    p: int
    a: int
    b: int
    n: int
    gx: int
    gy: int
    h: int = 1


@dataclass(frozen=True)
class ECPoint:
    x: int
    y: int
    inf: bool = False


SECP256K1 = CurveParams(
    p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    a=0,
    b=7,
    n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
    gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    h=1,
)


def _inv_mod(x: int, m: int) -> int:
    x = x % m
    return pow(x, -1, m)


def _is_on_curve(P: ECPoint, curve: CurveParams) -> bool:
    if P.inf:
        return True
    return (P.y * P.y - (P.x * P.x * P.x + curve.a * P.x + curve.b)) % curve.p == 0


def _point_add(P: ECPoint, Q: ECPoint, curve: CurveParams) -> ECPoint:
    if P.inf:
        return Q
    if Q.inf:
        return P
    if P.x == Q.x and (P.y != Q.y or P.y == 0):
        return ECPoint(0, 0, True)

    if P.x == Q.x and P.y == Q.y:
        lam = (3 * P.x * P.x + curve.a) * _inv_mod(2 * P.y, curve.p) % curve.p
    else:
        lam = (Q.y - P.y) * _inv_mod(Q.x - P.x, curve.p) % curve.p

    x3 = (lam * lam - P.x - Q.x) % curve.p
    y3 = (lam * (P.x - x3) - P.y) % curve.p
    return ECPoint(x3, y3, False)


def _point_mul(k: int, P: ECPoint, curve: CurveParams) -> ECPoint:
    if k % curve.n == 0 or P.inf:
        return ECPoint(0, 0, True)
    result = ECPoint(0, 0, True)
    addend = P
    scalar = k
    while scalar > 0:
        if scalar & 1:
            result = _point_add(result, addend, curve)
        addend = _point_add(addend, addend, curve)
        scalar >>= 1
    return result


def public_key_from_private(d: int, curve: CurveParams = SECP256K1) -> ECPoint:
    G = ECPoint(curve.gx, curve.gy)
    return _point_mul(d, G, curve)


def synthetic_ecdsa_signature(
    ur: int,
    uz: int,
    Q: ECPoint,
    curve: CurveParams = SECP256K1,
) -> tuple[ECDSASignature, int, ECPoint]:
    """Generate a valid (r, s, z) triple from (u_r, u_z) and public key.

    R = u_r * Q + u_z * G
    r = x(R) mod n
    s = r / u_r mod n
    z = u_z * s mod n
    """

    if not _is_on_curve(Q, curve):
        raise ValueError("public key Q is not on curve")
    if not (1 <= ur < curve.n) or not (1 <= uz < curve.n):
        raise ValueError("u_r and u_z must be in [1, n-1]")

    G = ECPoint(curve.gx, curve.gy)
    R = _point_add(_point_mul(ur, Q, curve), _point_mul(uz, G, curve), curve)
    if R.inf:
        raise ValueError("R is point at infinity; choose different u_r/u_z")
    r = R.x % curve.n
    if r == 0:
        raise ValueError("r == 0; choose different u_r/u_z")

    s = (r * _inv_mod(ur, curve.n)) % curve.n
    if s == 0:
        raise ValueError("s == 0; choose different u_r")

    z = (uz * s) % curve.n
    return ECDSASignature(r=r, s=s), z, R


def synthetic_ecdsa_batch(
    rng: RNG,
    count: int,
    Q: ECPoint,
    curve: CurveParams = SECP256K1,
) -> list[tuple[ECDSASignature, int]]:
    if count <= 0:
        raise ValueError("count must be positive")
    out = []
    while len(out) < count:
        ur = rng.random_uint(curve.n - 1) + 1
        uz = rng.random_uint(curve.n - 1) + 1
        try:
            sig, z, _ = synthetic_ecdsa_signature(ur, uz, Q, curve)
            out.append((sig, z))
        except ValueError:
            continue
    return out
