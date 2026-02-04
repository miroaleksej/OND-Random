from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG
from .backend import Backend, apply_cnot, apply_single_qubit, select_backend


# Basic single-qubit gates
H = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def rotation_x(theta: float) -> np.ndarray:
    c = np.cos(theta / 2.0)
    s = -1.0j * np.sin(theta / 2.0)
    return np.array([[c, s], [s, c]], dtype=complex)


def rotation_y(theta: float) -> np.ndarray:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rotation_z(theta: float) -> np.ndarray:
    return np.array([[np.exp(-0.5j * theta), 0.0], [0.0, np.exp(0.5j * theta)]], dtype=complex)


@dataclass
class QuantumState:
    n_qubits: int
    state: np.ndarray
    backend: Backend | None = None

    @classmethod
    def zero(cls, n_qubits: int, backend: Backend | None = None) -> "QuantumState":
        if n_qubits <= 0:
            raise ValueError("n_qubits must be positive")
        backend = backend or select_backend()
        size = 1 << n_qubits
        state = backend.xp.zeros(size, dtype=complex)
        state[0] = 1.0 + 0.0j
        return cls(n_qubits=n_qubits, state=state, backend=backend)

    def copy(self) -> "QuantumState":
        return QuantumState(self.n_qubits, self.state.copy(), self.backend)

    def apply_single_qubit(self, gate: np.ndarray, qubit: int) -> None:
        if qubit < 0 or qubit >= self.n_qubits:
            raise ValueError("qubit out of range")
        backend = self.backend or select_backend()
        self.state = apply_single_qubit(self.state, gate, qubit, self.n_qubits, xp=backend.xp)
        self.backend = backend

    def apply_single_qubit_batch(self, gates: list[np.ndarray], qubit: int) -> None:
        if not gates:
            return
        combined = gates[0]
        for g in gates[1:]:
            combined = g @ combined
        self.apply_single_qubit(combined, qubit)

    def apply_gate_sequence(self, ops: list[tuple[np.ndarray, int]]) -> None:
        for gate, qubit in ops:
            self.apply_single_qubit(gate, qubit)

    def apply_cnot(self, control: int, target: int) -> None:
        if control < 0 or control >= self.n_qubits:
            raise ValueError("control out of range")
        if target < 0 or target >= self.n_qubits:
            raise ValueError("target out of range")
        if control == target:
            raise ValueError("control and target must differ")
        backend = self.backend or select_backend()
        self.state = apply_cnot(self.state, control, target, self.n_qubits, xp=backend.xp)
        self.backend = backend

    def expectation_z(self, qubit: int) -> float:
        if qubit < 0 or qubit >= self.n_qubits:
            raise ValueError("qubit out of range")
        backend = self.backend or select_backend()
        xp = backend.xp
        size = 1 << self.n_qubits
        idx = xp.arange(size)
        mask = 1 << qubit
        probs = (self.state.real ** 2 + self.state.imag ** 2)
        signs = xp.where((idx & mask) == 0, 1.0, -1.0)
        exp = xp.sum(signs * probs)
        return float(exp.get() if hasattr(exp, "get") else exp)

    def measure_qubit(self, qubit: int, rng: RNG | None = None) -> int:
        if qubit < 0 or qubit >= self.n_qubits:
            raise ValueError("qubit out of range")
        if rng is None:
            rng = ONDMaxRNG(SystemRNG())
        backend = self.backend or select_backend()
        xp = backend.xp
        size = 1 << self.n_qubits
        mask = 1 << qubit
        idx = xp.arange(size)
        probs = (self.state.real ** 2 + self.state.imag ** 2)
        mask0 = (idx & mask) == 0
        p0 = xp.sum(probs[mask0])
        p0 = float(np.asarray(p0))
        # Sample from raw RNG bits
        r = rng.random_uint(1 << 64) / float(1 << 64)
        outcome = 0 if r < p0 else 1
        # Collapse
        norm = np.sqrt(p0) if outcome == 0 else np.sqrt(1.0 - p0)
        if norm == 0.0:
            raise ValueError("zero-probability measurement")
        if outcome == 0:
            keep = mask0
        else:
            keep = xp.logical_not(mask0)
        new_state = xp.where(keep, self.state / norm, xp.zeros_like(self.state))
        self.state = new_state
        self.backend = backend
        return outcome

    def measure_all(self, rng: RNG | None = None) -> int:
        if rng is None:
            rng = ONDMaxRNG(SystemRNG())
        backend = self.backend or select_backend()
        xp = backend.xp
        probs = (self.state.real ** 2 + self.state.imag ** 2)
        cumulative = xp.cumsum(probs)
        r = rng.random_uint(1 << 64) / float(1 << 64)
        if xp is np:
            cumulative_cpu = cumulative
        elif hasattr(cumulative, "get"):
            cumulative_cpu = cumulative.get()
        else:
            cumulative_cpu = np.asarray(cumulative)
        idx = int(np.searchsorted(cumulative_cpu, r, side="right"))
        if idx >= cumulative_cpu.size:
            idx = cumulative_cpu.size - 1
        # Collapse to basis state
        new_state = xp.zeros_like(self.state)
        if hasattr(new_state, "at"):
            new_state = new_state.at[idx].set(1.0 + 0.0j)
        else:
            new_state[idx] = 1.0 + 0.0j
        self.state = new_state
        self.backend = backend
        return idx

    def measure_shots(self, shots: int, rng: RNG | None = None) -> list[int]:
        if shots <= 0:
            raise ValueError("shots must be positive")
        if rng is None:
            rng = ONDMaxRNG(SystemRNG())
        counts = []
        for _ in range(shots):
            # Copy state for each shot to avoid collapse
            temp = self.copy()
            counts.append(temp.measure_all(rng=rng))
        return counts
