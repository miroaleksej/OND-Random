from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np


@dataclass
class Backend:
    name: str
    xp: Any
    available: bool


def _try_import_cupy() -> Backend:
    try:
        import cupy  # type: ignore

        return Backend(name="cupy", xp=cupy, available=True)
    except Exception:
        return Backend(name="cupy", xp=None, available=False)


def _try_import_jax() -> Backend:
    try:
        import jax.numpy as jnp  # type: ignore

        return Backend(name="jax", xp=jnp, available=True)
    except Exception:
        return Backend(name="jax", xp=None, available=False)


def available_backends() -> list[Backend]:
    backends = [Backend(name="numpy", xp=np, available=True)]
    backends.append(_try_import_cupy())
    backends.append(_try_import_jax())
    return backends


def select_backend(name: str | None = None) -> Backend:
    env = os.getenv("OND_BACKEND")
    if name is None and env:
        name = env
    if name == "auto":
        return auto_select_backend()
    backends = {b.name: b for b in available_backends()}
    if name is None:
        # prefer GPU if available
        if backends.get("cupy") and backends["cupy"].available:
            return backends["cupy"]
        if backends.get("jax") and backends["jax"].available:
            return backends["jax"]
        return backends["numpy"]
    if name not in backends or not backends[name].available:
        raise ValueError(f"backend '{name}' not available")
    return backends[name]


def apply_single_qubit(state, gate, qubit: int, n_qubits: int, xp=np):
    if qubit < 0 or qubit >= n_qubits:
        raise ValueError("qubit out of range")
    left = 1 << qubit
    right = 1 << (n_qubits - qubit - 1)
    psi = state.reshape(left, 2, right)
    # fast path: X or Z
    if xp is np:
        g = gate
        if np.allclose(g, np.array([[0, 1], [1, 0]], dtype=complex)):
            tmp = psi[:, 0, :].copy()
            psi[:, 0, :] = psi[:, 1, :]
            psi[:, 1, :] = tmp
            return state
        if np.allclose(g, np.array([[1, 0], [0, -1]], dtype=complex)):
            psi[:, 1, :] *= -1
            return state
    g = xp.asarray(gate)
    a = psi[:, 0, :]
    b = psi[:, 1, :]
    new0 = g[0, 0] * a + g[0, 1] * b
    new1 = g[1, 0] * a + g[1, 1] * b
    new = xp.stack([new0, new1], axis=1)
    return new.reshape(-1)


def apply_cnot(state, control: int, target: int, n_qubits: int, xp=np):
    if control < 0 or control >= n_qubits:
        raise ValueError("control out of range")
    if target < 0 or target >= n_qubits:
        raise ValueError("target out of range")
    if control == target:
        raise ValueError("control and target must differ")
    size = 1 << n_qubits
    idx = xp.arange(size)
    control_bit = (idx >> control) & 1
    idx_flipped = idx ^ (control_bit * (1 << target))
    return state[idx_flipped]


def benchmark_backend(n_qubits: int = 20, iters: int = 10) -> dict[str, float]:
    results = {}
    for backend in available_backends():
        if not backend.available:
            continue
        xp = backend.xp
        size = 1 << n_qubits
        state = xp.ones(size, dtype=complex) / np.sqrt(size)
        gate = xp.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / np.sqrt(2.0)
        t0 = time.time()
        for _ in range(iters):
            state = apply_single_qubit(state, gate, 0, n_qubits, xp=xp)
        if backend.name == "cupy":
            xp.cuda.Stream.null.synchronize()  # type: ignore
        t1 = time.time()
        results[backend.name] = (t1 - t0) / iters
    return results


def auto_select_backend(n_qubits: int = 20, iters: int = 5) -> Backend:
    results = benchmark_backend(n_qubits=n_qubits, iters=iters)
    if not results:
        return select_backend("numpy")
    best_name = min(results, key=results.get)
    return select_backend(best_name)
