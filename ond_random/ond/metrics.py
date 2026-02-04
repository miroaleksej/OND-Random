from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

@dataclass
class ONDProfile:
    h_rank: float
    h_sub: float
    h_branch: float
    rank: int
    n_samples: int
    dimension: int
    modulus: int | None

    def as_dict(self) -> Dict[str, float | int | None]:
        return {
            "H_rank": float(self.h_rank),
            "H_sub": float(self.h_sub),
            "H_branch": float(self.h_branch),
            "rank": int(self.rank),
            "n_samples": int(self.n_samples),
            "dimension": int(self.dimension),
            "modulus": int(self.modulus) if self.modulus is not None else None,
        }


def _centered_diff(U: np.ndarray, modulus: int | None) -> np.ndarray:
    if U.shape[0] < 2:
        return np.empty((0, U.shape[1]), dtype=float)
    if modulus is None:
        return (U[1:] - U[:-1]).astype(float)
    # Handle object arrays for big-int modular arithmetic
    if U.dtype == object:
        rows = []
        half = modulus / 2
        for i in range(U.shape[0] - 1):
            row = []
            for j in range(U.shape[1]):
                d = (int(U[i + 1, j]) - int(U[i, j])) % modulus
                if d > half:
                    d -= modulus
                row.append(float(d))
            rows.append(row)
        return np.array(rows, dtype=float)
    diff = (U[1:] - U[:-1]) % modulus
    diff = diff.astype(float)
    half = modulus / 2.0
    diff[diff > half] -= modulus
    return diff


def _rank_entropy(D: np.ndarray) -> Tuple[float, int]:
    if D.size == 0:
        return 0.0, 0
    s = np.linalg.svd(D, compute_uv=False)
    s = s[s > 0]
    if s.size == 0:
        return 0.0, 0
    p = s / s.sum()
    h = -np.sum(p * np.log(p))
    if p.size == 1:
        return 0.0, 1
    return float(h / np.log(p.size)), int(p.size)


def _subspace_occupancy(D: np.ndarray, bins: int, max_dim: int, modulus: int | None) -> float:
    if D.size == 0:
        return 0.0
    # SVD for principal directions
    u, s, vt = np.linalg.svd(D, full_matrices=False)
    tol = 1e-9 * s[0] if s.size else 0.0
    r = int(np.sum(s > tol))
    if r == 0:
        return 0.0
    proj_dim = min(r, max_dim)
    V = vt[:proj_dim].T
    Y = D @ V
    # Raw binning: use modulus if available, otherwise range-based binning
    if modulus is not None:
        span = float(modulus)
        bin_size = span / bins
        if bin_size <= 0:
            return 0.0
        # Shift to [0, modulus)
        Y = (Y + span / 2.0) % span
        idx = np.floor(Y / bin_size).astype(int)
        idx = np.clip(idx, 0, bins - 1)
    else:
        mins = Y.min(axis=0)
        maxs = Y.max(axis=0)
        span = maxs - mins
        span[span == 0] = 1.0
        idx = np.floor((Y - mins) / span * bins).astype(int)
        idx = np.clip(idx, 0, bins - 1)
    # Hash bin indices to counts
    counts = {}
    for row in idx:
        key = tuple(int(v) for v in row)
        counts[key] = counts.get(key, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p = np.array([c / total for c in counts.values()], dtype=float)
    h = -np.sum(p * np.log(p))
    log_total = proj_dim * np.log(bins)
    return float(h / log_total) if log_total > 0 else 0.0


def _branching_index(U: np.ndarray, modulus: int | None, branch_bins: int, mode: str = "raw") -> float:
    n = U.shape[0]
    if n < 2:
        return 0.0
    if mode not in {"raw", "delta"}:
        raise ValueError("branch_mode must be 'raw' or 'delta'")
    # Raw binning into discrete states (no normalization)
    if mode == "delta":
        X = _centered_diff(U, modulus=modulus)
        if X.shape[0] < 2:
            return 0.0
    else:
        X = U.astype(float)
    if modulus is not None:
        span = float(modulus)
        bin_size = span / branch_bins
        if bin_size <= 0:
            return 0.0
        X = X % span
        idx = np.floor(X / bin_size).astype(int)
        idx = np.clip(idx, 0, branch_bins - 1)
    else:
        mins = X.min(axis=0)
        maxs = X.max(axis=0)
        span = maxs - mins
        span[span == 0] = 1.0
        idx = np.floor((X - mins) / span * branch_bins).astype(int)
        idx = np.clip(idx, 0, branch_bins - 1)

    states = [tuple(int(v) for v in row) for row in idx]
    # Map state to index
    state_to_idx = {}
    state_ids = []
    for state in states:
        if state not in state_to_idx:
            state_to_idx[state] = len(state_to_idx)
        state_ids.append(state_to_idx[state])
    k = len(state_to_idx)
    if k <= 1:
        return 0.0

    transitions = {i: {} for i in range(k)}
    counts = np.zeros(k, dtype=int)
    for i in range(len(state_ids) - 1):
        a = state_ids[i]
        b = state_ids[i + 1]
        counts[a] += 1
        transitions[a][b] = transitions[a].get(b, 0) + 1

    entropies = []
    weights = []
    for a in range(k):
        total = counts[a]
        if total == 0:
            continue
        p = np.array([c / total for c in transitions[a].values()], dtype=float)
        h = -np.sum(p * np.log(p))
        entropies.append(h)
        weights.append(total)
    if not entropies:
        return 0.0
    h_weighted = float(np.average(entropies, weights=weights))
    return float(h_weighted / np.log(k)) if k > 1 else 0.0


def compute_profile(
    U: np.ndarray,
    modulus: int | None = None,
    bins: int = 16,
    max_subspace_dim: int = 6,
    branch_bins: int | None = None,
    branch_mode: str = "raw",
) -> ONDProfile:
    if U.ndim != 2:
        raise ValueError("U must be 2D array (samples x dimension)")
    D = _centered_diff(U, modulus)
    h_rank, rank = _rank_entropy(D)
    h_sub = _subspace_occupancy(D, bins=bins, max_dim=max_subspace_dim, modulus=modulus)
    if branch_bins is None:
        # Adaptive rule: branch_bins <= (N/10)^(1/d)
        n = U.shape[0]
        d = U.shape[1]
        if n <= 0 or d <= 0:
            branch_bins = 2
        else:
            branch_bins = max(2, int((n / 10.0) ** (1.0 / d)))
    h_branch = _branching_index(U, modulus=modulus, branch_bins=branch_bins, mode=branch_mode)
    return ONDProfile(
        h_rank=h_rank,
        h_sub=h_sub,
        h_branch=h_branch,
        rank=rank,
        n_samples=int(U.shape[0]),
        dimension=int(U.shape[1]),
        modulus=modulus,
    )
