from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG
from .lindblad_multi import MultiQubitHamiltonian, MultiQubitNoise, _single_op, _broadcast, Z2, SM


@dataclass
class TrajectoryResult:
    n_qubits: int
    steps: int
    trajectories: int
    dt: float
    expectations_z: list[float]
    expectations_z_std: list[float] | None = None
    expectations_z_sem: list[float] | None = None

    def as_dict(self) -> dict:
        data = {
            "n_qubits": self.n_qubits,
            "steps": self.steps,
            "trajectories": self.trajectories,
            "dt": self.dt,
            "expectations_z": self.expectations_z,
        }
        if self.expectations_z_std is not None:
            data["expectations_z_std"] = self.expectations_z_std
        if self.expectations_z_sem is not None:
            data["expectations_z_sem"] = self.expectations_z_sem
        return data


def _build_collapse_ops(n_qubits: int, noise: MultiQubitNoise) -> list[np.ndarray]:
    gamma1 = _broadcast(noise.gamma1, n_qubits, "gamma1")
    gamma_phi = _broadcast(noise.gamma_phi, n_qubits, "gamma_phi")
    ops = []
    for i in range(n_qubits):
        if gamma1[i] > 0.0:
            ops.append(np.sqrt(gamma1[i]) * _single_op(SM, n_qubits, i))
        if gamma_phi[i] > 0.0:
            ops.append(np.sqrt(gamma_phi[i]) * _single_op(Z2, n_qubits, i))
    return ops


def _expectation_z(psi: np.ndarray, n_qubits: int, qubit: int) -> float:
    size = 1 << n_qubits
    idx = np.arange(size)
    # Align with Lindblad operator ordering (qubit 0 is most significant)
    mask = 1 << (n_qubits - 1 - qubit)
    probs = (psi.real ** 2 + psi.imag ** 2)
    signs = np.where((idx & mask) == 0, 1.0, -1.0)
    return float(np.sum(signs * probs))


def simulate_trajectories(
    n_qubits: int,
    steps: int,
    dt: float,
    hamiltonian: MultiQubitHamiltonian | None = None,
    noise: MultiQubitNoise | None = None,
    trajectories: int = 100,
    rng: RNG | None = None,
    initial_state: np.ndarray | None = None,
) -> TrajectoryResult:
    if n_qubits <= 0:
        raise ValueError("n_qubits must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if dt <= 0:
        raise ValueError("dt must be positive")
    if trajectories <= 0:
        raise ValueError("trajectories must be positive")

    if rng is None:
        rng = ONDMaxRNG(SystemRNG())

    hamiltonian = hamiltonian or MultiQubitHamiltonian(n_qubits=n_qubits)
    noise = noise or MultiQubitNoise()

    H = hamiltonian.matrix()
    L_ops = _build_collapse_ops(n_qubits, noise)
    LdL = [L.conj().T @ L for L in L_ops]
    Heff = H - 0.5j * sum(LdL) if LdL else H

    size = 1 << n_qubits
    mean = np.zeros(n_qubits, dtype=float)
    m2 = np.zeros(n_qubits, dtype=float)
    count = 0

    for _ in range(trajectories):
        if initial_state is None:
            psi = np.zeros(size, dtype=complex)
            psi[0] = 1.0 + 0.0j
        else:
            if initial_state.shape != (size,):
                raise ValueError("initial_state has wrong shape")
            psi = initial_state.astype(complex).copy()
            norm0 = np.linalg.norm(psi)
            if norm0 == 0.0:
                raise ValueError("initial_state has zero norm")
            psi = psi / norm0

        for _ in range(steps):
            # Jump probabilities
            jump_probs = []
            p_total = 0.0
            for L in L_ops:
                v = L @ psi
                p = dt * float(np.vdot(v, v).real)
                jump_probs.append(p)
                p_total += p

            r = rng.random_uint(1 << 64) / float(1 << 64)
            if p_total > 0.0 and r < p_total:
                # Quantum jump
                r2 = r / p_total
                cumulative = 0.0
                chosen = 0
                for i, p in enumerate(jump_probs):
                    cumulative += p / p_total
                    if r2 <= cumulative:
                        chosen = i
                        break
                psi = L_ops[chosen] @ psi
            else:
                # No jump: non-Hermitian evolution
                psi = psi - 1.0j * dt * (Heff @ psi)

            # Normalize
            norm = np.linalg.norm(psi)
            if norm == 0.0:
                psi[0] = 1.0 + 0.0j
            else:
                psi = psi / norm

        count += 1
        for q in range(n_qubits):
            x = _expectation_z(psi, n_qubits, q)
            delta = x - mean[q]
            mean[q] += delta / count
            delta2 = x - mean[q]
            m2[q] += delta * delta2

    if count > 1:
        std = np.sqrt(m2 / (count - 1))
    else:
        std = np.zeros_like(mean)
    sem = std / np.sqrt(max(count, 1))
    return TrajectoryResult(
        n_qubits=n_qubits,
        steps=steps,
        trajectories=trajectories,
        dt=dt,
        expectations_z=[float(x) for x in mean],
        expectations_z_std=[float(x) for x in std],
        expectations_z_sem=[float(x) for x in sem],
    )
