from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG
from .statevector import QuantumState, H, X, Z, rotation_y


@dataclass
class BellResult:
    counts: dict[str, int]
    correlation: float


def bell_state_correlations(shots: int = 1000, rng: RNG | None = None) -> BellResult:
    """Create a Bell state and measure ZZ correlations."""
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    state = QuantumState.zero(2)
    state.apply_single_qubit(H, 0)
    state.apply_cnot(0, 1)

    counts = {"00": 0, "01": 0, "10": 0, "11": 0}
    for _ in range(shots):
        outcome = state.copy().measure_all(rng=rng)
        b0 = (outcome >> 0) & 1
        b1 = (outcome >> 1) & 1
        key = f"{b1}{b0}"  # qubit1 as MSB for readability
        counts[key] += 1

    # Correlation E = P(00)+P(11) - P(01)-P(10)
    total = float(shots)
    corr = (counts["00"] + counts["11"] - counts["01"] - counts["10"]) / total
    return BellResult(counts=counts, correlation=corr)


def rabi_oscillation(theta: float, steps: int, shots: int = 256, rng: RNG | None = None) -> list[float]:
    """Simulate a single-qubit Rabi oscillation around Y.

    Returns expectation values of Z after each step.
    """
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    results = []
    for k in range(steps):
        state = QuantumState.zero(1)
        state.apply_single_qubit(rotation_y(theta * k), 0)
        # Estimate expectation via sampling
        counts = {0: 0, 1: 0}
        for _ in range(shots):
            outcome = state.copy().measure_all(rng=rng)
            counts[outcome] += 1
        exp_z = (counts[0] - counts[1]) / float(shots)
        results.append(exp_z)
    return results


def quantum_random_walk(steps: int, shots: int = 256, rng: RNG | None = None) -> dict[int, float]:
    """Discrete-time quantum walk on a line with a 1-qubit coin.

    Returns probability distribution over positions.
    """
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    # Position register size
    pos_bits = max(1, int(np.ceil(np.log2(2 * steps + 1))))
    n = pos_bits + 1  # + coin
    pos_zero = 0

    counts = {}
    for _ in range(shots):
        state = QuantumState.zero(n)
        # initialize position |0> and coin |0>
        for _ in range(steps):
            # coin toss
            state.apply_single_qubit(H, 0)
            # shift: if coin=0 move left, coin=1 move right
            # brute-force apply shift by permuting amplitudes
            size = 1 << n
            new_state = np.zeros_like(state.state)
            for idx in range(size):
                coin = idx & 1
                pos = idx >> 1
                if coin == 0:
                    new_pos = pos - 1
                else:
                    new_pos = pos + 1
                # wrap within range [-(2^pos_bits)/2, ...] by modulo
                max_pos = 1 << pos_bits
                new_pos = new_pos % max_pos
                new_idx = (new_pos << 1) | coin
                new_state[new_idx] = state.state[idx]
            state.state = new_state
        outcome = state.measure_all(rng=rng)
        pos = outcome >> 1
        # map to signed position
        if pos >= (1 << (pos_bits - 1)):
            pos = pos - (1 << pos_bits)
        counts[pos] = counts.get(pos, 0) + 1

    total = float(shots)
    return {k: v / total for k, v in counts.items()}


def monte_carlo_integral(
    f: Callable[[np.ndarray], np.ndarray],
    a: float,
    b: float,
    samples: int,
    rng: RNG | None = None,
) -> float:
    """Monte Carlo estimate of integral f(x) dx on [a, b]."""
    if samples <= 0:
        raise ValueError("samples must be positive")
    if rng is None:
        rng = ONDMaxRNG(SystemRNG())
    # Use raw RNG to generate uniform floats via 64-bit integers
    u = np.empty(samples, dtype=float)
    for i in range(samples):
        u[i] = rng.random_uint(1 << 64) / float(1 << 64)
    x = a + (b - a) * u
    return float((b - a) * np.mean(f(x)))
