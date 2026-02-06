from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import numpy as np

from .embedding import ensure_2d, torus_embed_modular, unit_scale_modular


@dataclass(frozen=True)
class TopologyConfig:
    enabled: bool
    mode: str
    embedding: str
    maxdim: int
    persistence_rel: float
    persistence_min: float
    sample_size: int | None
    sample_seed: int
    bootstrap_samples: int
    bootstrap_seed: int


DEFAULT_TOPOLOGY_CONFIG = {
    "enabled": None,  # auto
    "mode": "points",
    "embedding": "auto",
    "maxdim": 2,
    "persistence_rel": 0.2,
    "persistence_min": 0.0,
    "sample_size": 512,
    "sample_seed": None,
    "bootstrap_samples": 30,
    "bootstrap_seed": 0,
}


def normalize_topology_config(config: Dict[str, Any] | None, *, profile: str | None) -> TopologyConfig:
    cfg = dict(DEFAULT_TOPOLOGY_CONFIG)
    if config:
        cfg.update({k: v for k, v in config.items() if v is not None})

    enabled = cfg.get("enabled")
    if enabled is None:
        enabled = profile in {"recommended", "dev"}

    sample_seed = cfg.get("sample_seed")
    if sample_seed is None:
        sample_seed = int(cfg.get("bootstrap_seed", 0))

    return TopologyConfig(
        enabled=bool(enabled),
        mode=str(cfg.get("mode", "points")),
        embedding=str(cfg.get("embedding", "auto")),
        maxdim=int(cfg.get("maxdim", 2)),
        persistence_rel=float(cfg.get("persistence_rel", 0.2)),
        persistence_min=float(cfg.get("persistence_min", 0.0)),
        sample_size=None if cfg.get("sample_size") in (None, 0) else int(cfg.get("sample_size")),
        sample_seed=int(sample_seed),
        bootstrap_samples=int(cfg.get("bootstrap_samples", 30)),
        bootstrap_seed=int(cfg.get("bootstrap_seed", 0)),
    )


def _try_import_ripser() -> tuple[Any | None, str | None]:
    try:
        from ripser import ripser  # type: ignore[import-not-found]

        return ripser, None
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        return None, str(exc)


def _centered_diff(U: np.ndarray, modulus: int | None) -> np.ndarray:
    if U.shape[0] < 2:
        return np.empty((0, U.shape[1]), dtype=float)
    if modulus is None:
        return (U[1:] - U[:-1]).astype(float)
    if U.dtype == object:
        rows: list[list[float]] = []
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


def _resolve_embedding(obs_space: Dict[str, Any], embedding: str) -> str:
    if embedding not in {"auto", "raw", "torus", "unit"}:
        raise ValueError("embedding must be auto|raw|torus|unit")
    if embedding != "auto":
        return embedding
    if obs_space.get("type") == "Z_mod_m":
        return "torus"
    return "raw"


def _prepare_point_cloud(U: np.ndarray, obs_space: Dict[str, Any], embedding: str) -> tuple[np.ndarray, str, str | None]:
    embedding = _resolve_embedding(obs_space, embedding)
    U2 = ensure_2d(U)
    if embedding == "raw":
        X = np.asarray(U2, dtype=float)
        return X, "raw", None
    if embedding == "torus":
        modulus = obs_space.get("modulus")
        if modulus is None:
            return np.empty((0, 0), dtype=float), "torus", "missing_modulus"
        X = torus_embed_modular(U2, int(modulus))
        return X, "torus", None
    if embedding == "unit":
        modulus = obs_space.get("modulus")
        if modulus is None:
            return np.empty((0, 0), dtype=float), "unit", "missing_modulus"
        X = unit_scale_modular(U2, int(modulus))
        return X, "unit", None
    return np.asarray(U2, dtype=float), embedding, None


def _subsample(X: np.ndarray, size: int | None, seed: int) -> tuple[np.ndarray, int]:
    n = X.shape[0]
    if n == 0:
        return X, 0
    if size is None or size >= n:
        return X, n
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=size, replace=False)
    return X[idx], int(size)


def _diagram_stats(dgm: np.ndarray, persistence_rel: float, persistence_min: float) -> Dict[str, float | int]:
    if dgm.size == 0:
        return {
            "finite_count": 0,
            "infinite_count": 0,
            "count": 0,
            "total_persistence": 0.0,
            "mean_persistence": 0.0,
            "max_persistence": 0.0,
            "entropy": 0.0,
            "threshold": max(0.0, float(persistence_min)),
        }
    births = dgm[:, 0]
    deaths = dgm[:, 1]
    finite_mask = np.isfinite(deaths)
    finite = dgm[finite_mask]
    infinite_count = int((~finite_mask).sum())
    if finite.size == 0:
        return {
            "finite_count": 0,
            "infinite_count": infinite_count,
            "count": 0,
            "total_persistence": 0.0,
            "mean_persistence": 0.0,
            "max_persistence": 0.0,
            "entropy": 0.0,
            "threshold": max(0.0, float(persistence_min)),
        }
    persistence = finite[:, 1] - finite[:, 0]
    max_persistence = float(np.max(persistence)) if persistence.size else 0.0
    threshold = max(float(persistence_min), float(persistence_rel) * max_persistence if max_persistence > 0 else 0.0)
    keep = persistence >= threshold
    keep_p = persistence[keep]
    count = int(keep_p.size)
    total = float(keep_p.sum()) if count else 0.0
    mean = float(total / count) if count else 0.0
    entropy = 0.0
    if total > 0:
        p = keep_p / total
        entropy = float(-np.sum(p * np.log(p + 1e-12)))
    return {
        "finite_count": int(finite.shape[0]),
        "infinite_count": infinite_count,
        "count": count,
        "total_persistence": total,
        "mean_persistence": mean,
        "max_persistence": max_persistence,
        "entropy": entropy,
        "threshold": threshold,
    }


def _layer_labels(layer: str, maxdim: int) -> List[str]:
    labels: List[str] = []
    for dim in range(maxdim + 1):
        labels.append(f"{layer}:H{dim}_count")
        labels.append(f"{layer}:H{dim}_total")
        labels.append(f"{layer}:H{dim}_entropy")
    return labels


def _layer_vector(stats: Dict[str, Any], maxdim: int) -> List[float]:
    vec: List[float] = []
    for dim in range(maxdim + 1):
        key = f"H{dim}"
        item = stats.get(key, {})
        vec.append(float(item.get("count", 0.0)))
        vec.append(float(item.get("total_persistence", 0.0)))
        vec.append(float(item.get("entropy", 0.0)))
    return vec


def _layer_names(mode: str) -> List[str]:
    if mode == "points":
        return ["points"]
    if mode == "delta":
        return ["delta"]
    if mode == "both":
        return ["points", "delta"]
    raise ValueError("mode must be points|delta|both")


def compute_topology_signature(
    U: np.ndarray,
    obs_space: Dict[str, Any],
    config: TopologyConfig,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "skipped",
        "reason": None,
        "mode": config.mode,
        "embedding": config.embedding,
        "maxdim": config.maxdim,
        "persistence_rel": config.persistence_rel,
        "persistence_min": config.persistence_min,
        "sample_size": config.sample_size,
        "n_samples": int(U.shape[0]),
    }

    ripser, err = _try_import_ripser()
    if ripser is None:
        result["reason"] = f"missing_ripser ({err})"
        return result

    layers: Dict[str, Any] = {}
    labels: List[str] = []
    vector: List[float] = []
    warnings: List[str] = []

    modulus = None
    if obs_space.get("type") == "Z_mod_m":
        modulus = obs_space.get("modulus")

    for layer in _layer_names(config.mode):
        if layer == "points":
            X, embed_used, prep_err = _prepare_point_cloud(U, obs_space, config.embedding)
            layer_embedding = embed_used
        else:
            D = _centered_diff(U, modulus=int(modulus) if modulus is not None else None)
            X = np.asarray(D, dtype=float)
            layer_embedding = "raw"
            prep_err = None

        if prep_err:
            layers[layer] = {"status": "skipped", "reason": prep_err, "embedding": layer_embedding}
            labels.extend(_layer_labels(layer, config.maxdim))
            vector.extend([0.0] * (config.maxdim + 1) * 3)
            continue

        if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] == 0:
            layers[layer] = {
                "status": "skipped",
                "reason": "insufficient_samples",
                "embedding": layer_embedding,
                "n_used": int(X.shape[0]) if X.ndim == 2 else 0,
            }
            labels.extend(_layer_labels(layer, config.maxdim))
            vector.extend([0.0] * (config.maxdim + 1) * 3)
            continue

        X = np.asarray(X, dtype=float)
        if not np.all(np.isfinite(X)):
            layers[layer] = {"status": "skipped", "reason": "non_finite_values", "embedding": layer_embedding}
            labels.extend(_layer_labels(layer, config.maxdim))
            vector.extend([0.0] * (config.maxdim + 1) * 3)
            continue

        X_use, n_used = _subsample(X, config.sample_size, config.sample_seed)
        if X_use.shape[0] < 2:
            layers[layer] = {
                "status": "skipped",
                "reason": "insufficient_samples",
                "embedding": layer_embedding,
                "n_used": int(X_use.shape[0]),
            }
            labels.extend(_layer_labels(layer, config.maxdim))
            vector.extend([0.0] * (config.maxdim + 1) * 3)
            continue

        dgms = ripser(X_use, maxdim=config.maxdim).get("dgms", [])
        stats: Dict[str, Any] = {}
        for dim in range(config.maxdim + 1):
            dgm = dgms[dim] if dim < len(dgms) else np.empty((0, 2), dtype=float)
            stats[f"H{dim}"] = _diagram_stats(dgm, config.persistence_rel, config.persistence_min)

        layer_result = {
            "status": "ok",
            "embedding": layer_embedding,
            "n_used": int(n_used),
            "dimensions": int(X_use.shape[1]),
            "H": stats,
        }
        layers[layer] = layer_result
        labels.extend(_layer_labels(layer, config.maxdim))
        vector.extend(_layer_vector(stats, config.maxdim))

    if not vector:
        result["reason"] = "no_layers_computed"
        return result

    result["status"] = "ok"
    result["layers"] = layers
    result["signature"] = {"vector": vector, "labels": labels}
    if warnings:
        result["warnings"] = warnings
    return result


def bootstrap_topology_vectors(
    U: np.ndarray,
    obs_space: Dict[str, Any],
    config: TopologyConfig,
) -> Tuple[List[np.ndarray], List[str]]:
    if config.bootstrap_samples <= 0:
        return [], []
    if U.shape[0] == 0:
        return [], []
    rng = np.random.default_rng(config.bootstrap_seed)
    n = U.shape[0]
    sample_size = config.sample_size or n
    vectors: List[np.ndarray] = []
    labels: List[str] = []

    for _ in range(config.bootstrap_samples):
        idx = rng.integers(0, n, size=min(sample_size, n))
        sample = U[idx]
        seed = int(rng.integers(0, 2**31 - 1))
        cfg = TopologyConfig(
            enabled=config.enabled,
            mode=config.mode,
            embedding=config.embedding,
            maxdim=config.maxdim,
            persistence_rel=config.persistence_rel,
            persistence_min=config.persistence_min,
            sample_size=config.sample_size,
            sample_seed=seed,
            bootstrap_samples=config.bootstrap_samples,
            bootstrap_seed=config.bootstrap_seed,
        )
        res = compute_topology_signature(sample, obs_space, cfg)
        sig = res.get("signature")
        if not sig:
            continue
        labels = sig.get("labels", [])
        vectors.append(np.array(sig.get("vector", []), dtype=float))
    return vectors, labels
