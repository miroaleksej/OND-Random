from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG


@dataclass
class GroverResult:
    n_items: int
    n_qubits: int
    iterations: int
    targets: list[int]
    success_prob: float
    measured_success: float
    counts: Dict[int, int]
    theta: float
    theoretical_amplitude: float

    def as_dict(self) -> Dict[str, object]:
        return {
            "n_items": self.n_items,
            "n_qubits": self.n_qubits,
            "iterations": self.iterations,
            "targets": self.targets,
            "success_prob": self.success_prob,
            "measured_success": self.measured_success,
            "counts": self.counts,
            "theta": self.theta,
            "theoretical_amplitude": self.theoretical_amplitude,
        }


def grover_iterations(n_items: int, n_qubits: int | None = None, n_solutions: int = 1) -> int:
    if n_items <= 1:
        return 0
    if n_solutions <= 0:
        raise ValueError("n_solutions must be positive")
    if n_qubits is None:
        n_qubits = math.ceil(math.log2(n_items))
    N = 1 << n_qubits
    return max(1, int(math.floor((math.pi / 4.0) * math.sqrt(N / n_solutions))))


def grover_theta(n_items: int, n_qubits: int | None = None, n_solutions: int = 1) -> float:
    if n_items <= 1:
        return 0.0
    if n_solutions <= 0:
        raise ValueError("n_solutions must be positive")
    if n_qubits is None:
        n_qubits = math.ceil(math.log2(n_items))
    N = 1 << n_qubits
    # sin(theta) = sqrt(M/N)
    return math.asin(math.sqrt(n_solutions / N))


def grover_state(
    targets: list[int],
    n_items: int,
    n_qubits: int | None = None,
    iterations: int | None = None,
) -> np.ndarray:
    if n_items <= 1:
        raise ValueError("n_items must be > 1")
    if n_qubits is None:
        n_qubits = math.ceil(math.log2(n_items))
    N = 1 << n_qubits
    if not targets:
        raise ValueError("targets must be non-empty")
    for t in targets:
        if t < 0 or t >= n_items:
            raise ValueError("targets must be in [0, n_items)")
    if iterations is None:
        iterations = grover_iterations(n_items, n_qubits=n_qubits, n_solutions=len(targets))

    # Uniform superposition over 2^n states
    state = np.ones(N, dtype=complex) / math.sqrt(N)

    for _ in range(iterations):
        # Oracle: phase flip on target states
        for t in targets:
            state[t] *= -1.0
        # Diffusion: inversion about mean (exact Grover diffusion)
        mean = state.mean()
        state = 2.0 * mean - state

    return state


def grover_measure(state: np.ndarray, shots: int = 1, rng: RNG | None = None) -> Dict[int, int]:
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    if shots <= 0:
        raise ValueError("shots must be positive")
    probs = (state.real ** 2 + state.imag ** 2)
    probs = probs / probs.sum()
    cumulative = np.cumsum(probs)
    counts: Dict[int, int] = {}
    for _ in range(shots):
        r = rng.random_uint(1 << 64) / float(1 << 64)
        idx = int(np.searchsorted(cumulative, r, side="right"))
        if idx >= cumulative.size:
            idx = cumulative.size - 1
        counts[idx] = counts.get(idx, 0) + 1
    return counts


def grover_search(
    target: int | None = None,
    targets: list[int] | None = None,
    n_items: int = 0,
    n_qubits: int | None = None,
    iterations: int | None = None,
    shots: int = 1,
    rng: RNG | None = None,
) -> GroverResult:
    if n_items <= 1:
        raise ValueError("n_items must be > 1")
    if targets is None:
        if target is None:
            raise ValueError("target or targets must be provided")
        targets = [int(target)]
    if n_qubits is None:
        n_qubits = math.ceil(math.log2(n_items))
    theta = grover_theta(n_items, n_qubits=n_qubits, n_solutions=len(targets))
    state = grover_state(targets, n_items, n_qubits=n_qubits, iterations=iterations)
    prob = float(sum((state[t].real ** 2 + state[t].imag ** 2) for t in targets))
    counts = grover_measure(state, shots=shots, rng=rng)
    success = sum(counts.get(t, 0) for t in targets) / float(shots)
    k = iterations if iterations is not None else grover_iterations(n_items, n_qubits=n_qubits, n_solutions=len(targets))
    theoretical_amplitude = float(math.sin((2 * k + 1) * theta))
    return GroverResult(
        n_items=n_items,
        n_qubits=n_qubits,
        iterations=k,
        targets=targets,
        success_prob=prob,
        measured_success=success,
        counts=counts,
        theta=theta,
        theoretical_amplitude=theoretical_amplitude,
    )
