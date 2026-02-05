from __future__ import annotations

import math

import numpy as np


def ensure_2d(U: np.ndarray) -> np.ndarray:
    if U.ndim == 1:
        return U.reshape(-1, 1)
    if U.ndim != 2:
        raise ValueError("U must be 1D or 2D array")
    return U


def delay_embed_series(series: np.ndarray, embed_dim: int, delay: int = 1, stride: int = 1) -> np.ndarray:
    """Delay-embed a scalar series into an observation matrix.

    Returns U with shape (M, embed_dim), where:
      U[i, j] = series[i*stride + j*delay]
    """
    if embed_dim <= 0:
        raise ValueError("embed_dim must be positive")
    if delay <= 0:
        raise ValueError("delay must be positive")
    if stride <= 0:
        raise ValueError("stride must be positive")
    x = np.asarray(series, dtype=float).reshape(-1)
    n = x.shape[0]
    needed = (embed_dim - 1) * delay + 1
    if n < needed:
        return np.empty((0, embed_dim), dtype=float)
    starts = range(0, n - needed + 1, stride)
    windows = [x[i : i + needed : delay] for i in starts]
    return np.array(windows, dtype=float)


def unit_scale_modular(U: np.ndarray, modulus: int) -> np.ndarray:
    """Maps modular integers into [0, 1) floats (per coordinate)."""
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    U2 = ensure_2d(U)
    out = np.empty(U2.shape, dtype=float)
    n = float(modulus)
    for i in range(U2.shape[0]):
        for j in range(U2.shape[1]):
            out[i, j] = (int(U2[i, j]) % modulus) / n
    return out


def torus_embed_modular(U: np.ndarray, modulus: int) -> np.ndarray:
    """Embeds modular integers onto a torus using cos/sin per coordinate.

    For each scalar x (mod modulus), emit (cos(2πx/n), sin(2πx/n)).
    Output shape: (N, 2*d).
    """
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    U2 = ensure_2d(U)
    n = float(modulus)
    out = np.empty((U2.shape[0], U2.shape[1] * 2), dtype=float)
    two_pi = 2.0 * math.pi
    for i in range(U2.shape[0]):
        for j in range(U2.shape[1]):
            t = (int(U2[i, j]) % modulus) / n
            theta = two_pi * t
            out[i, 2 * j] = math.cos(theta)
            out[i, 2 * j + 1] = math.sin(theta)
    return out

