from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG


@dataclass
class ShorResult:
    N: int
    a: int
    factors: Tuple[int, int] | None
    order: int | None
    measured_y: int | None
    M: int
    n_qubits: int
    shots: int
    gamma1: float | None = None
    gamma_phi: float | None = None
    noise_strength: float | None = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "N": self.N,
            "a": self.a,
            "factors": self.factors,
            "order": self.order,
            "measured_y": self.measured_y,
            "M": self.M,
            "n_qubits": self.n_qubits,
            "shots": self.shots,
            "gamma1": self.gamma1,
            "gamma_phi": self.gamma_phi,
            "noise_strength": self.noise_strength,
        }


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _continued_fraction(x: float, max_terms: int = 20) -> List[int]:
    terms = []
    for _ in range(max_terms):
        a = math.floor(x)
        terms.append(a)
        frac = x - a
        if frac < 1e-12:
            break
        x = 1.0 / frac
    return terms


def _convergents(terms: List[int]) -> List[Tuple[int, int]]:
    conv = []
    num0, den0 = 1, 0
    num1, den1 = terms[0], 1
    conv.append((num1, den1))
    for a in terms[1:]:
        num2 = a * num1 + num0
        den2 = a * den1 + den0
        conv.append((num2, den2))
        num0, den0 = num1, den1
        num1, den1 = num2, den2
    return conv


def order_of_a(a: int, N: int) -> int | None:
    if _gcd(a, N) != 1:
        return None
    r = 1
    val = a % N
    while val != 1:
        val = (val * a) % N
        r += 1
        if r > N:
            return None
    return r


def _periodic_superposition_amplitudes(r: int, M: int, x0: int = 0) -> np.ndarray:
    # amplitudes after QFT for state |x0 + k r>, k=0..L-1
    L = (M - 1 - x0) // r + 1
    amps = np.zeros(M, dtype=complex)
    # compute for each y via geometric sum
    for y in range(M):
        phase = 2.0j * math.pi * y * r / M
        exp_phase = np.exp(phase)
        if abs(1 - exp_phase) < 1e-12:
            # denominator ~0 -> sum=L
            s = L
        else:
            s = (1 - np.exp(phase * L)) / (1 - exp_phase)
        amps[y] = np.exp(2.0j * math.pi * y * x0 / M) * s / math.sqrt(L * M)
    return amps


def _sample_from_probs(probs: np.ndarray, shots: int, rng: RNG) -> List[int]:
    cumulative = np.cumsum(probs)
    out = []
    for _ in range(shots):
        r = rng.random_uint(1 << 64) / float(1 << 64)
        idx = int(np.searchsorted(cumulative, r, side="right"))
        if idx >= cumulative.size:
            idx = cumulative.size - 1
        out.append(idx)
    return out


def _estimate_order_from_measurement(y: int, M: int, a: int, N: int) -> int | None:
    if y == 0:
        return None
    frac = y / M
    terms = _continued_fraction(frac, max_terms=20)
    for num, den in _convergents(terms):
        if den <= 0 or den > N:
            continue
        if pow(a, den, N) == 1:
            return den
    return None


def _apply_noise_to_probs(probs: np.ndarray, n_qubits: int, gamma1: float, gamma_phi: float) -> tuple[np.ndarray, float]:
    # Effective depolarizing noise on measurement distribution (approximation).
    # noise_strength = 1 - exp(-(gamma1 + gamma_phi) * n_qubits)
    noise_strength = 1.0 - math.exp(-(gamma1 + gamma_phi) * max(1, n_qubits))
    noise_strength = min(max(noise_strength, 0.0), 0.99)
    M = probs.size
    uniform = np.ones(M, dtype=float) / M
    noisy = (1.0 - noise_strength) * probs + noise_strength * uniform
    noisy = noisy / noisy.sum()
    return noisy, noise_strength


def shor_factor(
    N: int,
    a: int,
    shots: int = 20,
    rng: RNG | None = None,
    gamma1: float | None = None,
    gamma_phi: float | None = None,
) -> ShorResult:
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    if N <= 1:
        raise ValueError("N must be > 1")
    if a <= 1 or a >= N:
        raise ValueError("a must be in (1, N)")

    g = _gcd(a, N)
    if g != 1:
        return ShorResult(N=N, a=a, factors=(g, N // g), order=None, measured_y=None, M=0, n_qubits=0, shots=shots)

    n_qubits = math.ceil(math.log2(N))
    t = 2 * n_qubits
    M = 1 << t

    # use period length r computed classically (ideal statevector)
    r = order_of_a(a, N)
    if r is None:
        return ShorResult(N=N, a=a, factors=None, order=None, measured_y=None, M=M, n_qubits=t, shots=shots)

    amps = _periodic_superposition_amplitudes(r, M, x0=0)
    probs = (amps.real ** 2 + amps.imag ** 2)
    probs = probs / probs.sum()
    noise_strength = None
    if gamma1 is not None or gamma_phi is not None:
        g1 = float(gamma1 or 0.0)
        gp = float(gamma_phi or 0.0)
        probs, noise_strength = _apply_noise_to_probs(probs, n_qubits=t, gamma1=g1, gamma_phi=gp)

    samples = _sample_from_probs(probs, shots=shots, rng=rng)
    for y in samples:
        r_est = _estimate_order_from_measurement(y, M, a, N)
        if r_est is None or r_est % 2 == 1:
            continue
        x = pow(a, r_est // 2, N)
        if x == N - 1:
            continue
        p = _gcd(x - 1, N)
        q = _gcd(x + 1, N)
        if p not in (1, N) and q not in (1, N):
            return ShorResult(
                N=N,
                a=a,
                factors=(p, q),
                order=r_est,
                measured_y=y,
                M=M,
                n_qubits=t,
                shots=shots,
                gamma1=gamma1,
                gamma_phi=gamma_phi,
                noise_strength=noise_strength,
            )

    return ShorResult(
        N=N,
        a=a,
        factors=None,
        order=r,
        measured_y=None,
        M=M,
        n_qubits=t,
        shots=shots,
        gamma1=gamma1,
        gamma_phi=gamma_phi,
        noise_strength=noise_strength,
    )
