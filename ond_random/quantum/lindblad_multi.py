from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG


I2 = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
X2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Y2 = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
Z2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
SM = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)  # |0><1|


def _broadcast(values: float | Sequence[float], n: int, name: str) -> list[float]:
    if isinstance(values, (int, float)):
        return [float(values)] * n
    if len(values) != n:
        raise ValueError(f"{name} must have length {n}")
    return [float(v) for v in values]


def _kron_all(ops: Sequence[np.ndarray]) -> np.ndarray:
    out = ops[0]
    for op in ops[1:]:
        out = np.kron(out, op)
    return out


def _single_op(op: np.ndarray, n: int, qubit: int) -> np.ndarray:
    ops = [I2] * n
    ops[qubit] = op
    return _kron_all(ops)


def _pair_op(op1: np.ndarray, op2: np.ndarray, n: int, q1: int, q2: int) -> np.ndarray:
    ops = [I2] * n
    ops[q1] = op1
    ops[q2] = op2
    return _kron_all(ops)


@dataclass
class MultiQubitHamiltonian:
    """H = 0.5 * sum_i (wx_i X_i + wy_i Y_i + wz_i Z_i) + sum_{i<j} J_ij Z_i Z_j"""

    n_qubits: int
    omega_x: float | Sequence[float] = 0.0
    omega_y: float | Sequence[float] = 0.0
    omega_z: float | Sequence[float] = 1.0
    couplings_zz: dict[tuple[int, int], float] | None = None

    def matrix(self) -> np.ndarray:
        n = self.n_qubits
        wx = _broadcast(self.omega_x, n, "omega_x")
        wy = _broadcast(self.omega_y, n, "omega_y")
        wz = _broadcast(self.omega_z, n, "omega_z")
        H = np.zeros((1 << n, 1 << n), dtype=complex)
        for i in range(n):
            if wx[i] != 0.0:
                H += 0.5 * wx[i] * _single_op(X2, n, i)
            if wy[i] != 0.0:
                H += 0.5 * wy[i] * _single_op(Y2, n, i)
            if wz[i] != 0.0:
                H += 0.5 * wz[i] * _single_op(Z2, n, i)
        if self.couplings_zz:
            for (i, j), J in self.couplings_zz.items():
                if i == j:
                    continue
                H += J * _pair_op(Z2, Z2, n, i, j)
        return H


@dataclass
class MultiQubitNoise:
    gamma1: float | Sequence[float] = 0.0
    gamma_phi: float | Sequence[float] = 0.0


class LindbladSystem:
    """Multi-qubit density-matrix Lindblad simulator."""

    def __init__(
        self,
        n_qubits: int,
        hamiltonian: MultiQubitHamiltonian | None = None,
        noise: MultiQubitNoise | None = None,
    ):
        if n_qubits <= 0:
            raise ValueError("n_qubits must be positive")
        self.n_qubits = n_qubits
        self.hamiltonian = hamiltonian or MultiQubitHamiltonian(n_qubits=n_qubits)
        self.noise = noise or MultiQubitNoise()
        self.dim = 1 << n_qubits
        self.rho = np.zeros((self.dim, self.dim), dtype=complex)
        self.rho[0, 0] = 1.0 + 0.0j

        # Precompute operators
        self._H = self.hamiltonian.matrix()
        self._L = self._build_lindblad_ops()

    def _build_lindblad_ops(self) -> list[np.ndarray]:
        n = self.n_qubits
        gamma1 = _broadcast(self.noise.gamma1, n, "gamma1")
        gamma_phi = _broadcast(self.noise.gamma_phi, n, "gamma_phi")
        ops = []
        for i in range(n):
            if gamma1[i] > 0.0:
                ops.append(np.sqrt(gamma1[i]) * _single_op(SM, n, i))
            if gamma_phi[i] > 0.0:
                ops.append(np.sqrt(gamma_phi[i]) * _single_op(Z2, n, i))
        return ops

    def reset(self) -> None:
        self.rho = np.zeros((self.dim, self.dim), dtype=complex)
        self.rho[0, 0] = 1.0 + 0.0j

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.rho = self.rho + dt * self._drho(self.rho)
        tr = np.trace(self.rho)
        if tr != 0:
            self.rho = self.rho / tr

    def step_rk4(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        k1 = self._drho(self.rho)
        k2 = self._drho(self.rho + 0.5 * dt * k1)
        k3 = self._drho(self.rho + 0.5 * dt * k2)
        k4 = self._drho(self.rho + dt * k3)
        self.rho = self.rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        tr = np.trace(self.rho)
        if tr != 0:
            self.rho = self.rho / tr

    def _drho(self, rho: np.ndarray) -> np.ndarray:
        comm = self._H @ rho - rho @ self._H
        drho = -1.0j * comm
        for L in self._L:
            drho += L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
        return drho

    def expectation_z(self, qubit: int) -> float:
        if qubit < 0 or qubit >= self.n_qubits:
            raise ValueError("qubit out of range")
        Z = _single_op(Z2, self.n_qubits, qubit)
        val = np.trace(self.rho @ Z).real
        return float(val)

    def measure(self, rng: RNG | None = None) -> int:
        if rng is None:
            rng = ONDMaxRNG(SystemRNG())
        probs = (self.rho.diagonal().real).clip(0.0, 1.0)
        cumulative = np.cumsum(probs)
        r = rng.random_uint(1 << 64) / float(1 << 64)
        idx = int(np.searchsorted(cumulative, r, side="right"))
        if idx >= cumulative.size:
            idx = cumulative.size - 1
        new_rho = np.zeros_like(self.rho)
        new_rho[idx, idx] = 1.0 + 0.0j
        self.rho = new_rho
        return idx
