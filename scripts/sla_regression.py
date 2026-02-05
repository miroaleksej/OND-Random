from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ond_random import ObservationMap, compute_profile
from ond_random.rng.base import RNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.structured import MaskedRNG, BoundedRNG


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _merge_case(defaults: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    merged = {**defaults, **case}
    merged_max_abs = {**defaults.get("max_abs", {}), **case.get("max_abs", {})}
    merged["max_abs"] = merged_max_abs
    return merged


def _rng_from_case(case: Dict[str, Any]) -> RNG:
    name = case.get("rng", "system")
    if name == "system":
        return SystemRNG()
    if name == "lcg":
        return LCGRNG(seed=int(case.get("seed", 1)))
    if name == "xorshift":
        return XorShiftRNG(seed1=int(case.get("seed", 1)), seed2=int(case.get("seed2", 2)))
    if name == "chacha20":
        key_hex = case.get("key_hex")
        if key_hex:
            key = bytes.fromhex(str(key_hex))
            return ChaCha20RNG(key=key)
        seed = int(case.get("seed", 1))
        return ChaCha20RNG.from_seed(seed.to_bytes(8, "big"))
    if name == "quantum":
        model = QuantumNoiseModel(
            bias=float(case.get("bias", 0.0)),
            drift_sigma=float(case.get("drift_sigma", 1e-3)),
            drift_rho=float(case.get("drift_rho", 0.999)),
            memory=float(case.get("memory", 0.0)),
            phase_sigma=float(case.get("phase_sigma", 0.0)),
        )
        return QuantumEmulatorRNG(seed=case.get("seed"), model=model)
    if name in ("ondmax", "masked", "bounded"):
        source_name = case.get("source", "system")
        source_case = {**case, "rng": source_name}
        source_rng = _rng_from_case(source_case)
        if name == "ondmax":
            return ONDMaxRNG(source=source_rng)
        if name == "masked":
            return MaskedRNG(source=source_rng, mask_low_bits=int(case.get("mask_low_bits", 4)))
        return BoundedRNG(source=source_rng, bound_bits=int(case.get("bound_bits", 12)))
    raise ValueError(f"unknown rng: {name}")


def _load_baseline(path: str) -> Dict[str, float]:
    data = _load_json(path)
    return {
        "H_rank": float(data["H_rank"]),
        "H_sub": float(data["H_sub"]),
        "H_branch": float(data["H_branch"]),
    }


def _compute_profile(case: Dict[str, Any]) -> Dict[str, float]:
    obs = ObservationMap(
        dimension=int(case["dimension"]),
        word_bits=int(case["word_bits"]),
        stride=int(case.get("stride", 1)),
    )
    rng = _rng_from_case(case)
    U = obs.from_rng(rng, samples=int(case["samples"]))
    modulus = obs.modulus if bool(case.get("modulus", False)) else None
    profile = compute_profile(
        U,
        modulus=modulus,
        bins=int(case.get("bins", 16)),
        max_subspace_dim=int(case.get("max_subspace_dim", 6)),
        branch_bins=case.get("branch_bins"),
        branch_mode=str(case.get("branch_mode", "raw")),
    )
    data = profile.as_dict()
    return {
        "H_rank": float(data["H_rank"]),
        "H_sub": float(data["H_sub"]),
        "H_branch": float(data["H_branch"]),
    }


def _metric_vector(metrics: Dict[str, float]) -> np.ndarray:
    return np.array([metrics["H_rank"], metrics["H_sub"], metrics["H_branch"]], dtype=float)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="docs/large_sample_sla.json")
    parser.add_argument("--out", default="data/reports/sla_regression.json")
    args = parser.parse_args()

    cfg = _load_json(args.config)
    defaults = cfg.get("defaults", {})
    cases = cfg.get("cases", [])
    if not cases:
        raise ValueError("SLA config must include at least one case")

    results = []
    for case in cases:
        merged = _merge_case(defaults, case)
        baseline_path = merged.get("baseline_profile")
        if not baseline_path:
            raise ValueError(f"case '{merged.get('id', 'unknown')}' missing baseline_profile")

        baseline = _load_baseline(baseline_path)
        current = _compute_profile(merged)

        diffs = {k: abs(current[k] - baseline[k]) for k in baseline}
        l2 = float(np.linalg.norm(_metric_vector(current) - _metric_vector(baseline)))

        max_abs = merged.get("max_abs", {})
        max_l2 = merged.get("max_l2")

        abs_ok = all(diffs[k] <= float(max_abs.get(k, float("inf"))) for k in diffs)
        l2_ok = True if max_l2 is None else l2 <= float(max_l2)
        ok = abs_ok and l2_ok

        results.append(
            {
                "id": merged.get("id", baseline_path),
                "baseline_profile": baseline_path,
                "samples": int(merged["samples"]),
                "metrics": current,
                "baseline": baseline,
                "diffs": diffs,
                "l2": l2,
                "thresholds": {"max_abs": max_abs, "max_l2": max_l2},
                "ok": ok,
            }
        )

    status = "PASS" if all(r["ok"] for r in results) else "FAIL"
    payload = {"status": status, "config": args.config, "results": results}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
