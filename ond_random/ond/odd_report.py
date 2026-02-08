from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

import numpy as np

from .metrics import compute_profile_details
from .observations_jsonl import read_observations_jsonl
from .orbit_spectrum import bootstrap_orbit_vectors, compute_orbit_spectrum, normalize_orbit_config
from .topology import bootstrap_topology_vectors, compute_topology_signature, normalize_topology_config


@dataclass
class BaselineResult:
    baseline_id: str
    mean_vector: np.ndarray
    thresholds: Dict[str, float]


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return f"sha256:{_sha256_hex(text.encode('utf-8'))}"


def hash_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"sha256:{_sha256_hex(payload)}"


def _bootstrap_indices(rng: np.random.Generator, n: int, size: int) -> np.ndarray:
    return rng.integers(0, n, size=size)


def _metric_vector(details: Dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            float(details["rank"]["rho"]),
            float(details["subspace"]["rho"]),
            float(details["branching"]["H"]),
        ],
        dtype=float,
    )


def _bootstrap_samples(
    U: np.ndarray,
    *,
    modulus: int | None,
    bins: int,
    max_subspace_dim: int,
    branch_bins: int | None,
    branch_mode: str,
    samples: int,
    seed: int,
) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    n = U.shape[0]
    if n == 0:
        return []
    results = []
    for _ in range(samples):
        idx = _bootstrap_indices(rng, n, n)
        sample = U[idx]
        results.append(
            compute_profile_details(
                sample,
                modulus=modulus,
                bins=bins,
                max_subspace_dim=max_subspace_dim,
                branch_bins=branch_bins,
                branch_mode=branch_mode,
            )
        )
    return results


def _ci95(
    values: Iterable[float],
    center: float | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
) -> List[float]:
    arr = np.array(list(values), dtype=float)
    if arr.size == 0:
        return [0.0, 0.0]
    if center is None:
        lo = float(np.percentile(arr, 2.5))
        hi = float(np.percentile(arr, 97.5))
        if min_value is not None:
            lo = max(lo, min_value)
            hi = max(hi, min_value)
        if max_value is not None:
            lo = min(lo, max_value)
            hi = min(hi, max_value)
        return [lo, hi]
    diffs = np.abs(arr - float(center))
    radius = float(np.percentile(diffs, 95.0))
    lo = float(center - radius)
    hi = float(center + radius)
    if min_value is not None:
        lo = max(lo, min_value)
        hi = max(hi, min_value)
    if max_value is not None:
        lo = min(lo, max_value)
        hi = min(hi, max_value)
    return [lo, hi]


def _baseline_thresholds(distances: np.ndarray, percentiles: Tuple[float, float, float]) -> Dict[str, float]:
    if distances.size == 0:
        return {"green": 0.0, "yellow": 0.0, "red": 0.0}
    return {
        "green": float(np.percentile(distances, percentiles[0])),
        "yellow": float(np.percentile(distances, percentiles[1])),
        "red": float(np.percentile(distances, percentiles[2])),
    }


def _classify(distance: float, thresholds: Dict[str, float]) -> str:
    if distance <= thresholds.get("green", 0.0):
        return "Within Baseline Envelope"
    if distance <= thresholds.get("yellow", 0.0):
        return "Deviating"
    return "Strong Deviation"


def _build_run(run_id: str | None = None, created_at: str | None = None, timezone_name: str = "Etc/UTC") -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "run_id": run_id or f"{now.isoformat()}#{uuid4().hex}",
        "created_at": created_at or now.isoformat(),
        "timezone": timezone_name,
    }


def _ensure_pi_spec_hash(meta: Dict[str, Any]) -> str:
    if "pi_spec_hash" in meta and isinstance(meta["pi_spec_hash"], str) and meta["pi_spec_hash"]:
        return meta["pi_spec_hash"]
    payload = {
        "pi_id": meta.get("pi_id"),
        "pi_version": meta.get("pi_version"),
        "obs_space": meta.get("obs_space"),
    }
    return hash_json(payload)


def build_baseline_from_observations(
    observations_path: str,
    *,
    baseline_id: str,
    bins: int,
    max_subspace_dim: int,
    branch_bins: int | None,
    branch_mode: str,
    bootstrap_samples: int,
    bootstrap_seed: int,
    percentiles: Tuple[float, float, float],
) -> BaselineResult:
    meta, U, _ = read_observations_jsonl(observations_path)
    modulus = None
    obs_space = meta.get("obs_space") if isinstance(meta, dict) else None
    if isinstance(obs_space, dict) and obs_space.get("type") == "Z_mod_m":
        modulus = int(obs_space["modulus"])

    details = compute_profile_details(
        U,
        modulus=modulus,
        bins=bins,
        max_subspace_dim=max_subspace_dim,
        branch_bins=branch_bins,
        branch_mode=branch_mode,
    )
    mean_vector = _metric_vector(details)

    boot = _bootstrap_samples(
        U,
        modulus=modulus,
        bins=bins,
        max_subspace_dim=max_subspace_dim,
        branch_bins=branch_bins,
        branch_mode=branch_mode,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    dist_samples = np.array([np.linalg.norm(_metric_vector(b) - mean_vector) for b in boot], dtype=float)
    thresholds = _baseline_thresholds(dist_samples, percentiles)
    return BaselineResult(baseline_id=baseline_id, mean_vector=mean_vector, thresholds=thresholds)


def build_ond_art_report(
    observations_path: str,
    *,
    baseline_observations: str | None = None,
    baseline_report: Dict[str, Any] | None = None,
    baseline_id: str = "baseline-1",
    baseline_percentiles: Tuple[float, float, float] = (50.0, 80.0, 95.0),
    bins: int = 16,
    max_subspace_dim: int = 6,
    branch_bins: int | None = None,
    branch_mode: str = "raw",
    bootstrap_samples: int = 200,
    bootstrap_seed: int = 0,
    topology: Dict[str, Any] | None = None,
    orbit_spectrum: Dict[str, Any] | None = None,
    protocol: str = "custom",
    scheme: str = "custom",
    params: Dict[str, Any] | None = None,
    public_context_hash: str | None = None,
    order: str = "custom",
    message_policy: str = "custom",
    spec_profile: str | None = "core",
    method_version: str | None = "unknown",
    spec_version: str | None = "0.1",
    schema_version: str | None = "0.1",
    notes: List[str] | None = None,
    run_id: str | None = None,
    created_at: str | None = None,
    timezone_name: str = "Etc/UTC",
) -> Dict[str, Any]:
    meta, U, invalid_count = read_observations_jsonl(observations_path)
    obs_space = meta.get("obs_space") if isinstance(meta, dict) else None
    if not isinstance(obs_space, dict):
        obs_space = {"type": "R^d", "d": int(U.shape[1])}
    modulus = None
    if obs_space.get("type") == "Z_mod_m":
        modulus = int(obs_space["modulus"])

    pi_id = meta.get("pi_id") or "pi:custom"
    pi_version = meta.get("pi_version") or "0.0.0"
    pi_spec_hash = _ensure_pi_spec_hash(meta)

    if public_context_hash is None:
        if isinstance(meta, dict) and meta.get("public_context_hash"):
            public_context_hash = str(meta["public_context_hash"])
        elif isinstance(meta, dict) and meta.get("context"):
            public_context_hash = hash_json(meta["context"])
        else:
            public_context_hash = hash_text("")

    details = compute_profile_details(
        U,
        modulus=modulus,
        bins=bins,
        max_subspace_dim=max_subspace_dim,
        branch_bins=branch_bins,
        branch_mode=branch_mode,
    )

    boot = _bootstrap_samples(
        U,
        modulus=modulus,
        bins=bins,
        max_subspace_dim=max_subspace_dim,
        branch_bins=branch_bins,
        branch_mode=branch_mode,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )

    rank_rhos = [b["rank"]["rho"] for b in boot]
    sub_rhos = [b["subspace"]["rho"] for b in boot]
    branch_H = [b["branching"]["H"] for b in boot]

    metrics = {
        "rank": {
            "H": float(details["rank"]["H"]),
            "rho": float(details["rank"]["rho"]),
            "ci95": _ci95(rank_rhos, center=float(details["rank"]["rho"]), min_value=0.0, max_value=1.0),
            "svd_settings": {"eps": 1e-9},
        },
        "subspace": {
            "H": float(details["subspace"]["H"]),
            "rho": float(details["subspace"]["rho"]),
            "ci95": _ci95(sub_rhos, center=float(details["subspace"]["rho"]), min_value=0.0, max_value=1.0),
            "binning": {
                "b": int(details["subspace"]["bins"]),
                "M_occ": int(details["subspace"]["nonempty"]),
            },
        },
        "branching": {
            "H": float(details["branching"]["H"]),
            "ci95": _ci95(branch_H, center=float(details["branching"]["H"]), min_value=0.0),
            "clustering": {
                "method": "grid",
                "K": int(details["branching"]["K"] or 1),
                "seed": int(bootstrap_seed),
            },
        },
    }

    topology_result: Dict[str, Any] | None = None
    topology_baseline: Dict[str, Any] | None = None
    topo_cfg = normalize_topology_config(topology, profile=spec_profile)
    if topo_cfg.enabled:
        topology_result = compute_topology_signature(U, obs_space, topo_cfg)

    orbit_result: Dict[str, Any] | None = None
    orbit_baseline: Dict[str, Any] | None = None
    orbit_cfg = normalize_orbit_config(orbit_spectrum, profile=spec_profile)
    if orbit_cfg.enabled:
        orbit_result = compute_orbit_spectrum(U, obs_space, orbit_cfg)

    baseline = None
    baseline_mean_vector: np.ndarray | None = None
    if baseline_observations:
        base = build_baseline_from_observations(
            baseline_observations,
            baseline_id=baseline_id,
            bins=bins,
            max_subspace_dim=max_subspace_dim,
            branch_bins=branch_bins,
            branch_mode=branch_mode,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            percentiles=baseline_percentiles,
        )
        baseline_mean_vector = base.mean_vector
        thresholds = base.thresholds
    elif baseline_report:
        ref_vec = np.array(
            [
                float(baseline_report["metrics"]["rank"]["rho"]),
                float(baseline_report["metrics"]["subspace"]["rho"]),
                float(baseline_report["metrics"]["branching"]["H"]),
            ],
            dtype=float,
        )
        baseline_mean_vector = ref_vec
        thresholds = baseline_report.get("baseline", {}).get("thresholds", {"green": 0.0, "yellow": 0.0, "red": 0.0})
    else:
        thresholds = None

    if baseline_mean_vector is not None:
        dist = float(np.linalg.norm(_metric_vector(details) - baseline_mean_vector))
        dist_ci = _ci95(
            [float(np.linalg.norm(_metric_vector(b) - baseline_mean_vector)) for b in boot],
            center=dist,
            min_value=0.0,
        )
        baseline = {
            "baseline_id": baseline_id,
            "distance": dist,
            "distance_ci95": dist_ci,
            "thresholds": thresholds or {"green": 0.0, "yellow": 0.0, "red": 0.0},
            "classification": _classify(dist, thresholds or {"green": 0.0, "yellow": 0.0, "red": 0.0}),
        }

    if topo_cfg.enabled and topology_result and topology_result.get("signature"):
        if baseline_observations:
            base_meta, base_U, _ = read_observations_jsonl(baseline_observations)
            base_obs_space = base_meta.get("obs_space") if isinstance(base_meta, dict) else None
            if not isinstance(base_obs_space, dict):
                base_obs_space = obs_space
            base_topo = compute_topology_signature(base_U, base_obs_space, topo_cfg)
            base_sig = base_topo.get("signature") if isinstance(base_topo, dict) else None
            cur_sig = topology_result.get("signature")
            if base_sig and cur_sig:
                base_vec = np.array(base_sig.get("vector", []), dtype=float)
                cur_vec = np.array(cur_sig.get("vector", []), dtype=float)
                if base_vec.size == cur_vec.size and base_vec.size > 0:
                    boot_vecs, _ = bootstrap_topology_vectors(base_U, base_obs_space, topo_cfg)
                    dist_samples = np.array(
                        [
                            float(np.linalg.norm(v - base_vec))
                            for v in boot_vecs
                            if v.shape == base_vec.shape
                        ],
                        dtype=float,
                    )
                    thresholds = _baseline_thresholds(dist_samples, baseline_percentiles)
                    dist = float(np.linalg.norm(cur_vec - base_vec))
                    dist_ci = _ci95(dist_samples, center=dist, min_value=0.0)
                    topology_baseline = {
                        "baseline_id": baseline_id,
                        "distance": dist,
                        "distance_ci95": dist_ci,
                        "thresholds": thresholds,
                        "classification": _classify(dist, thresholds),
                    }
        elif baseline_report:
            base_topology = baseline_report.get("topology") if isinstance(baseline_report, dict) else None
            base_sig = None
            base_thresholds = None
            if isinstance(base_topology, dict):
                base_sig = base_topology.get("signature")
                base_thresholds = base_topology.get("baseline", {}).get("thresholds")
            cur_sig = topology_result.get("signature")
            if base_sig and cur_sig:
                base_vec = np.array(base_sig.get("vector", []), dtype=float)
                cur_vec = np.array(cur_sig.get("vector", []), dtype=float)
                if base_vec.size == cur_vec.size and base_vec.size > 0:
                    dist = float(np.linalg.norm(cur_vec - base_vec))
                    boot_vecs, _ = bootstrap_topology_vectors(U, obs_space, topo_cfg)
                    dist_samples = np.array(
                        [
                            float(np.linalg.norm(v - base_vec))
                            for v in boot_vecs
                            if v.shape == base_vec.shape
                        ],
                        dtype=float,
                    )
                    dist_ci = _ci95(dist_samples, center=dist, min_value=0.0)
                    classification = "Unknown"
                    thresholds = None
                    if isinstance(base_thresholds, dict):
                        thresholds = base_thresholds
                        classification = _classify(dist, thresholds)
                    topology_baseline = {
                        "baseline_id": baseline_id,
                        "distance": dist,
                        "distance_ci95": dist_ci,
                        "thresholds": thresholds,
                        "classification": classification,
                    }

    if orbit_cfg.enabled and orbit_result and orbit_result.get("signature"):
        if baseline_observations:
            base_meta, base_U, _ = read_observations_jsonl(baseline_observations)
            base_obs_space = base_meta.get("obs_space") if isinstance(base_meta, dict) else None
            if not isinstance(base_obs_space, dict):
                base_obs_space = obs_space
            base_orbit = compute_orbit_spectrum(base_U, base_obs_space, orbit_cfg)
            base_sig = base_orbit.get("signature") if isinstance(base_orbit, dict) else None
            cur_sig = orbit_result.get("signature")
            if base_sig and cur_sig:
                base_vec = np.array(base_sig.get("vector", []), dtype=float)
                cur_vec = np.array(cur_sig.get("vector", []), dtype=float)
                if base_vec.size == cur_vec.size and base_vec.size > 0:
                    boot_vecs, _ = bootstrap_orbit_vectors(base_U, base_obs_space, orbit_cfg)
                    dist_samples = np.array(
                        [
                            float(np.linalg.norm(v - base_vec))
                            for v in boot_vecs
                            if v.shape == base_vec.shape
                        ],
                        dtype=float,
                    )
                    thresholds = _baseline_thresholds(dist_samples, baseline_percentiles)
                    dist = float(np.linalg.norm(cur_vec - base_vec))
                    dist_ci = _ci95(dist_samples, center=dist, min_value=0.0)
                    orbit_baseline = {
                        "baseline_id": baseline_id,
                        "distance": dist,
                        "distance_ci95": dist_ci,
                        "thresholds": thresholds,
                        "classification": _classify(dist, thresholds),
                    }
        elif baseline_report:
            base_orbit = baseline_report.get("orbit_spectrum") if isinstance(baseline_report, dict) else None
            base_sig = None
            base_thresholds = None
            if isinstance(base_orbit, dict):
                base_sig = base_orbit.get("signature")
                base_thresholds = base_orbit.get("baseline", {}).get("thresholds")
            cur_sig = orbit_result.get("signature")
            if base_sig and cur_sig:
                base_vec = np.array(base_sig.get("vector", []), dtype=float)
                cur_vec = np.array(cur_sig.get("vector", []), dtype=float)
                if base_vec.size == cur_vec.size and base_vec.size > 0:
                    dist = float(np.linalg.norm(cur_vec - base_vec))
                    boot_vecs, _ = bootstrap_orbit_vectors(U, obs_space, orbit_cfg)
                    dist_samples = np.array(
                        [
                            float(np.linalg.norm(v - base_vec))
                            for v in boot_vecs
                            if v.shape == base_vec.shape
                        ],
                        dtype=float,
                    )
                    dist_ci = _ci95(dist_samples, center=dist, min_value=0.0)
                    classification = "Unknown"
                    thresholds = None
                    if isinstance(base_thresholds, dict):
                        thresholds = base_thresholds
                        classification = _classify(dist, thresholds)
                    orbit_baseline = {
                        "baseline_id": baseline_id,
                        "distance": dist,
                        "distance_ci95": dist_ci,
                        "thresholds": thresholds,
                        "classification": classification,
                    }

    report = {
        "spec": {
            "name": "OND-ART",
            "version": "0.1",
            "spec_version": spec_version or "0.1",
            "schema_version": schema_version or "0.1",
        },
        "run": _build_run(run_id=run_id, created_at=created_at, timezone_name=timezone_name),
        "context": {
            "protocol": protocol,
            "scheme": scheme,
            "params": params or {},
            "public_context_hash": public_context_hash,
        },
        "data": {
            "N": int(U.shape[0]),
            "order": order,
            "message_policy": message_policy,
            "invalid_count": int(invalid_count),
        },
        "pi": {
            "pi_id": pi_id,
            "pi_version": pi_version,
            "pi_spec_hash": pi_spec_hash,
            "obs_space": obs_space,
        },
        "bootstrap": {
            "B": int(bootstrap_samples),
            "method": "percentile",
            "unit": "U",
            "block_length": 0,
        },
        "metrics": metrics,
        "baseline": baseline,
        "notes": notes or ["Diagnostic only; no security claim."],
    }
    if topology_result:
        if topology_baseline:
            topology_result["baseline"] = topology_baseline
        report["topology"] = topology_result
    if orbit_result:
        if orbit_baseline:
            orbit_result["baseline"] = orbit_baseline
        report["orbit_spectrum"] = orbit_result
    if spec_profile:
        report["spec"]["profile"] = spec_profile
    if method_version:
        report["spec"]["x-method_version"] = method_version
    return report
