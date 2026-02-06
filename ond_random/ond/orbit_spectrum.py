from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import math

import numpy as np

from .embedding import ensure_2d


@dataclass(frozen=True)
class OrbitSpectrumConfig:
    enabled: bool
    topk: int
    include_zero: bool
    bootstrap_samples: int
    bootstrap_seed: int


DEFAULT_ORBIT_CONFIG = {
    "enabled": None,  # auto
    "topk": 8,
    "include_zero": True,
    "bootstrap_samples": 30,
    "bootstrap_seed": 0,
}


def normalize_orbit_config(config: Dict[str, Any] | None, *, profile: str | None) -> OrbitSpectrumConfig:
    cfg = dict(DEFAULT_ORBIT_CONFIG)
    if config:
        cfg.update({k: v for k, v in config.items() if v is not None})

    enabled = cfg.get("enabled")
    if enabled is None:
        enabled = profile in {"recommended", "dev"}

    return OrbitSpectrumConfig(
        enabled=bool(enabled),
        topk=int(cfg.get("topk", 8)),
        include_zero=bool(cfg.get("include_zero", True)),
        bootstrap_samples=int(cfg.get("bootstrap_samples", 30)),
        bootstrap_seed=int(cfg.get("bootstrap_seed", 0)),
    )


def _gcd3(a: int, b: int, c: int) -> int:
    return math.gcd(math.gcd(abs(a), abs(b)), abs(c))


def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, x, y = _egcd(b % a, a)
    return g, y - (b // a) * x, x


def _modinv(a: int, n: int) -> int | None:
    if n == 0:
        return None
    a = int(a) % n
    if a == 0:
        return None
    g, x, _ = _egcd(a, n)
    if g != 1:
        return None
    return x % n


def _projective_direction(dr: int, dz: int, modulus: int) -> Tuple[str, Dict[str, Any]]:
    if dr == 0 and dz == 0:
        return "zero", {
            "type": "zero",
            "a": 0,
            "b": 0,
            "modulus": int(modulus),
            "gcd": int(modulus),
        }

    g = _gcd3(dr, dz, modulus)
    n1 = modulus // g
    if n1 <= 0:
        n1 = 1
    a = (dr // g) % n1
    b = (dz // g) % n1
    inv_a = _modinv(a, n1)
    if inv_a is not None:
        slope = (b * inv_a) % n1
        return (
            f"slope:{int(slope)}@{int(n1)}",
            {
                "type": "slope",
                "slope": int(slope),
                "a": int(a),
                "b": int(b),
                "modulus": int(n1),
                "gcd": int(g),
                "inverse": "a",
            },
        )
    return (
        f"pair:{int(a)}:{int(b)}@{int(n1)}",
        {
            "type": "pair",
            "a": int(a),
            "b": int(b),
            "modulus": int(n1),
            "gcd": int(g),
            "inverse": None,
        },
    )


def _delta_rows(U: np.ndarray, modulus: int) -> List[Tuple[int, int]]:
    U2 = ensure_2d(U)
    if U2.shape[0] < 2:
        return []
    rows: List[Tuple[int, int]] = []
    for i in range(U2.shape[0] - 1):
        dr = (int(U2[i + 1, 0]) - int(U2[i, 0])) % modulus
        dz = (int(U2[i + 1, 1]) - int(U2[i, 1])) % modulus
        rows.append((dr, dz))
    return rows


def _entropy_bits(counts: List[int]) -> float:
    total = float(sum(counts))
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p, 2)
    return float(h)


def _connection_vector(deltas: List[Tuple[int, int]], modulus: int) -> Dict[str, Any]:
    if not deltas:
        return {"components": [], "norm": 0.0}
    two_pi = 2.0 * math.pi
    sum_cos = [0.0, 0.0]
    sum_sin = [0.0, 0.0]
    n = float(modulus)
    for dr, dz in deltas:
        for idx, val in enumerate((dr, dz)):
            theta = two_pi * (val % modulus) / n
            sum_cos[idx] += math.cos(theta)
            sum_sin[idx] += math.sin(theta)
    total = float(len(deltas))
    mean_cos = [c / total for c in sum_cos]
    mean_sin = [s / total for s in sum_sin]
    components = [mean_cos[0], mean_sin[0], mean_cos[1], mean_sin[1]]
    norm = float(math.sqrt(sum(v * v for v in components)))
    return {"components": components, "norm": norm}


def compute_orbit_spectrum(U: np.ndarray, obs_space: Dict[str, Any], config: OrbitSpectrumConfig) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "skipped",
        "reason": None,
        "topk": config.topk,
        "include_zero": config.include_zero,
        "n_samples": int(U.shape[0]),
    }

    if not config.enabled:
        result["reason"] = "disabled"
        return result

    if obs_space.get("type") != "Z_mod_m":
        result["reason"] = "obs_space_not_Z_mod_m"
        return result
    modulus = obs_space.get("modulus")
    if modulus is None:
        result["reason"] = "missing_modulus"
        return result
    modulus = int(modulus)
    if modulus <= 0:
        result["reason"] = "invalid_modulus"
        return result

    U2 = ensure_2d(U)
    if U2.shape[1] != 2:
        result["reason"] = "requires_dimension_2"
        return result

    deltas = _delta_rows(U2, modulus)
    if not deltas:
        result["reason"] = "insufficient_samples"
        return result

    counts: Dict[str, int] = {}
    info: Dict[str, Dict[str, Any]] = {}
    l_sum: Dict[str, int] = {}
    l_min: Dict[str, int] = {}
    l_max: Dict[str, int] = {}
    zero_count = 0

    for dr, dz in deltas:
        if dr == 0 and dz == 0:
            zero_count += 1
            if not config.include_zero:
                continue
        key, direction = _projective_direction(dr, dz, modulus)
        counts[key] = counts.get(key, 0) + 1
        if key not in info:
            info[key] = direction
        g = _gcd3(dr, dz, modulus)
        L = modulus // g if g > 0 else 0
        l_sum[key] = l_sum.get(key, 0) + L
        l_min[key] = min(l_min.get(key, L), L)
        l_max[key] = max(l_max.get(key, L), L)

    if not counts:
        result["reason"] = "no_classes"
        return result

    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    total = sum(counts.values())
    probs = [c / total for _, c in items]
    entropy = _entropy_bits([c for _, c in items])
    unique = len(items)
    max_entropy = math.log(unique, 2) if unique > 0 else 0.0
    structure_bits = max(0.0, float(max_entropy - entropy))
    top1 = float(probs[0]) if probs else 0.0
    top2 = float(probs[1]) if len(probs) > 1 else 0.0
    zero_share = float(zero_count) / float(len(deltas)) if deltas else 0.0

    spectrum: List[Dict[str, Any]] = []
    for key, count in items[: max(config.topk, 0)]:
        p = count / total
        L_mean = l_sum.get(key, 0) / count if count > 0 else 0.0
        spectrum.append(
            {
                "class_id": key,
                "count": int(count),
                "p": float(p),
                "direction": info.get(key, {}),
                "cycle_length": {
                    "mean": float(L_mean),
                    "min": int(l_min.get(key, 0)),
                    "max": int(l_max.get(key, 0)),
                },
            }
        )

    total_L = sum(l_sum.values())
    mean_L = float(total_L / total) if total > 0 else 0.0
    mean_L_log2 = float(math.log(mean_L, 2)) if mean_L > 0 else 0.0

    type_label = "T2"
    if unique <= 1:
        type_label = "T0"
    elif unique == 2:
        type_label = "T1"

    signature_labels = [
        "orbit:H_class",
        "orbit:H0_max",
        "orbit:I_structure",
        "orbit:p1",
        "orbit:p2",
        "orbit:unique_classes",
        "orbit:zero_share",
        "orbit:log2_mean_cycle",
    ]
    signature_vector = [
        float(entropy),
        float(max_entropy),
        float(structure_bits),
        float(top1),
        float(top2),
        float(unique),
        float(zero_share),
        float(mean_L_log2),
    ]

    result.update(
        {
            "status": "ok",
            "delta": {
                "count": int(len(deltas)),
                "zero_count": int(zero_count),
                "nonzero_count": int(len(deltas) - zero_count),
            },
            "summary": {
                "type": type_label,
                "unique_classes": int(unique),
                "entropy_bits": float(entropy),
                "max_entropy_bits": float(max_entropy),
                "structure_bits": float(structure_bits),
                "dominant_share": float(top1),
                "second_share": float(top2),
                "zero_share": float(zero_share),
                "mean_cycle_length": float(mean_L),
            },
            "spectrum": spectrum,
            "projective_space": {"type": "P^1(Z_n)", "modulus": int(modulus)},
            "information_bound_bits": float(math.log(modulus, 2)),
            "connection_vector": _connection_vector(deltas, modulus),
            "signature": {"vector": signature_vector, "labels": signature_labels},
        }
    )
    return result


def bootstrap_orbit_vectors(
    U: np.ndarray,
    obs_space: Dict[str, Any],
    config: OrbitSpectrumConfig,
) -> Tuple[List[np.ndarray], List[str]]:
    if config.bootstrap_samples <= 0:
        return [], []
    if U.shape[0] == 0:
        return [], []
    rng = np.random.default_rng(config.bootstrap_seed)
    n = U.shape[0]
    vectors: List[np.ndarray] = []
    labels: List[str] = []

    for _ in range(config.bootstrap_samples):
        idx = rng.integers(0, n, size=n)
        sample = U[idx]
        res = compute_orbit_spectrum(sample, obs_space, config)
        sig = res.get("signature")
        if not sig:
            continue
        labels = sig.get("labels", [])
        vectors.append(np.array(sig.get("vector", []), dtype=float))
    return vectors, labels
