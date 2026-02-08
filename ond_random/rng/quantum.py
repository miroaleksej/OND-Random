from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .base import RNG

try:
    from scipy.signal import lfilter as _lfilter
except Exception:
    _lfilter = None


@dataclass
class QuantumNoiseModel:
    """Noise model for a quantum measurement emulator.

    bias: constant offset from 0.5
    drift_sigma: random-walk noise standard deviation
    drift_rho: AR(1) persistence of drift
    memory: correlation with previous bit (0..0.5)
    phase_sigma: instantaneous phase noise (per bit)
    clamp_eps: probability clamp to avoid extremes
    """

    bias: float = 0.0
    drift_sigma: float = 1e-3
    drift_rho: float = 0.999
    memory: float = 0.0
    phase_sigma: float = 0.0
    clamp_eps: float = 1e-6

    def validate(self) -> None:
        if not (-0.5 < self.bias < 0.5):
            raise ValueError("bias must be in (-0.5, 0.5)")
        if not (0.0 <= self.memory <= 0.5):
            raise ValueError("memory must be in [0, 0.5]")
        if not (0.0 <= self.drift_rho <= 1.0):
            raise ValueError("drift_rho must be in [0, 1]")
        if self.drift_sigma < 0.0:
            raise ValueError("drift_sigma must be non-negative")
        if self.phase_sigma < 0.0:
            raise ValueError("phase_sigma must be non-negative")
        if not (0.0 < self.clamp_eps < 0.5):
            raise ValueError("clamp_eps must be in (0, 0.5)")


class QuantumEmulatorRNG(RNG):
    """Quantum measurement emulator with configurable noise model."""

    def __init__(self, seed: int | None = None, model: QuantumNoiseModel | None = None):
        self._rng = np.random.default_rng(seed)
        self._model = model or QuantumNoiseModel()
        self._model.validate()
        self._drift = 0.0
        self._last_bit: int | None = None

    @property
    def model(self) -> QuantumNoiseModel:
        return self._model

    def _drift_series(self, n_bits: int) -> np.ndarray:
        m = self._model
        if n_bits <= 0:
            return np.empty(0, dtype=np.float64)

        rho = float(m.drift_rho)
        sigma = float(m.drift_sigma)

        if sigma == 0.0:
            if rho == 0.0:
                self._drift = 0.0
                return np.zeros(n_bits, dtype=np.float64)
            if rho == 1.0:
                return np.full(n_bits, self._drift, dtype=np.float64)
            steps = np.arange(1, n_bits + 1, dtype=np.float64)
            drift = self._drift * np.power(rho, steps)
            self._drift = float(drift[-1])
            return drift

        eps = self._rng.normal(size=n_bits)
        if _lfilter is not None:
            zi = np.array([rho * self._drift], dtype=np.float64)
            drift, _ = _lfilter([sigma], [1.0, -rho], eps, zi=zi)
            self._drift = float(drift[-1])
            return np.asarray(drift, dtype=np.float64)

        drift = np.empty(n_bits, dtype=np.float64)
        cur = float(self._drift)
        for i, e in enumerate(eps):
            cur = rho * cur + sigma * float(e)
            drift[i] = cur
        self._drift = float(cur)
        return drift

    def _random_bytes_vectorized(self, n: int) -> bytes:
        m = self._model
        n_bits = n * 8

        p = np.full(n_bits, 0.5 + m.bias, dtype=np.float64)
        p += self._drift_series(n_bits)
        if m.phase_sigma > 0.0:
            p += m.phase_sigma * self._rng.normal(size=n_bits)
        np.clip(p, m.clamp_eps, 1.0 - m.clamp_eps, out=p)

        bits = (self._rng.random(n_bits) < p).astype(np.uint8)
        if bits.size:
            self._last_bit = int(bits[-1])
        return np.packbits(bits, bitorder="big").tobytes()

    def _next_bit(self) -> int:
        m = self._model
        # Update drift as AR(1)
        if m.drift_sigma > 0.0:
            self._drift = m.drift_rho * self._drift + m.drift_sigma * self._rng.normal()
        else:
            self._drift = m.drift_rho * self._drift

        memory_term = 0.0
        if self._last_bit is not None and m.memory > 0.0:
            memory_term = m.memory if self._last_bit == 1 else -m.memory

        phase_term = m.phase_sigma * self._rng.normal() if m.phase_sigma > 0.0 else 0.0

        p = 0.5 + m.bias + self._drift + memory_term + phase_term
        p = max(m.clamp_eps, min(1.0 - m.clamp_eps, p))
        bit = 1 if self._rng.random() < p else 0
        self._last_bit = bit
        return bit

    def random_bytes(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("n must be non-negative")
        if n == 0:
            return b""

        if self._model.memory == 0.0:
            return self._random_bytes_vectorized(n)

        out = bytearray(n)
        for i in range(n):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | self._next_bit()
            out[i] = byte
        return bytes(out)
