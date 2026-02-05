from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..rng.base import RNG
from ..rng.extractor import ONDMaxRNG
from ..rng.system import SystemRNG


@dataclass
class QubitHamiltonian:
    """Two-level system Hamiltonian H = 0.5 * (omega_x X + omega_y Y + omega_z Z)."""

    omega_x: float = 0.0
    omega_y: float = 0.0
    omega_z: float = 1.0

    def matrix(self) -> np.ndarray:
        X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
        Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        return 0.5 * (self.omega_x * X + self.omega_y * Y + self.omega_z * Z)


@dataclass
class QubitNoise:
    """Lindblad noise rates for a single qubit.

    gamma1: amplitude damping (T1)
    gamma_phi: pure dephasing (Tphi)
    """

    gamma1: float = 0.0
    gamma_phi: float = 0.0


class LindbladQubit:
    """Density-matrix simulation for a noisy two-level system."""

    def __init__(self, hamiltonian: QubitHamiltonian | None = None, noise: QubitNoise | None = None):
        self.h = hamiltonian or QubitHamiltonian()
        self.noise = noise or QubitNoise()
        self.rho = np.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=complex)

    def reset(self) -> None:
        self.rho = np.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=complex)

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.rho = self.rho + dt * self._drho(self.rho)
        # Renormalize trace
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
        H = self.h.matrix()

        # Unitary part: -i [H, rho]
        comm = H @ rho - rho @ H
        drho = -1.0j * comm

        # Lindblad operators
        gamma1 = self.noise.gamma1
        gamma_phi = self.noise.gamma_phi
        if gamma1 > 0.0:
            # Amplitude damping L = sqrt(gamma1) * sigma-
            sm = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
            L = np.sqrt(gamma1) * sm
            drho += L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
        if gamma_phi > 0.0:
            # Dephasing L = sqrt(gamma_phi) * Z
            Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
            L = np.sqrt(gamma_phi) * Z
            drho += L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
        return drho

    def expectation_z(self) -> float:
        Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        val = np.trace(self.rho @ Z).real
        return float(val)

    def measure(self, rng: RNG | None = None) -> int:
        if rng is None:
            rng = ONDMaxRNG(SystemRNG())
        p0 = float(self.rho[0, 0].real)
        p0 = max(0.0, min(1.0, p0))
        r = rng.random_uint(1 << 64) / float(1 << 64)
        outcome = 0 if r < p0 else 1
        # collapse
        if outcome == 0:
            self.rho = np.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=complex)
        else:
            self.rho = np.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=complex)
        return outcome


def simulate_relaxation(
    t_max: float,
    steps: int,
    gamma1: float,
    gamma_phi: float,
    omega_z: float = 1.0,
    method: str = "rk4",
) -> list[float]:
    """Simulate Z-expectation under relaxation/dephasing."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    method = method.lower().strip()
    if method not in ("euler", "rk4"):
        raise ValueError("method must be 'euler' or 'rk4'")
    dt = t_max / steps
    model = LindbladQubit(
        hamiltonian=QubitHamiltonian(omega_z=omega_z),
        noise=QubitNoise(gamma1=gamma1, gamma_phi=gamma_phi),
    )
    results = []
    for _ in range(steps):
        if method == "rk4":
            model.step_rk4(dt)
        else:
            model.step(dt)
        results.append(model.expectation_z())
    return results
