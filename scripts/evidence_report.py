from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from ond_random import ObservationMap, compute_profile
from ond_random.ond.benchmark import ONDClass, ReferenceProfile, load_reference_profiles
from ond_random.rng.base import RNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.structured import MaskedRNG, BoundedRNG


def _rng_from_name(name: str, *, seed: int | None = None, seed2: int | None = None) -> RNG:
    if name == "system":
        return SystemRNG()
    if name == "lcg":
        return LCGRNG(seed=1 if seed is None else seed)
    if name == "xorshift":
        s1 = 1 if seed is None else seed
        s2 = 2 if seed2 is None else seed2
        return XorShiftRNG(seed1=s1, seed2=s2)
    if name == "chacha20":
        seed_val = 1 if seed is None else seed
        return ChaCha20RNG.from_seed(int(seed_val).to_bytes(8, "big"))
    if name == "quantum":
        seed_val = 1 if seed is None else seed
        return QuantumEmulatorRNG(seed=seed_val, model=QuantumNoiseModel())
    if name == "ondmax":
        return ONDMaxRNG(SystemRNG())
    if name == "masked":
        return MaskedRNG(SystemRNG(), mask_low_bits=4)
    if name == "bounded":
        return BoundedRNG(SystemRNG(), bound_bits=12)
    raise ValueError(f"unknown rng: {name}")


def _load_reference(path: str) -> ReferenceProfile | None:
    p = Path(path)
    if not p.exists():
        return None
    refs = load_reference_profiles(path)
    for ref in refs:
        if ref.ond_class == ONDClass.I:
            return ref
    return refs[0] if refs else None


def _profile_metrics(
    rng: RNG,
    samples: int,
    dimension: int,
    word_bits: int,
    stride: int,
    modulus: bool,
    bins: int,
    max_subspace_dim: int,
    branch_bins: int | None,
    branch_mode: str,
) -> Dict[str, float]:
    obs = ObservationMap(dimension=dimension, word_bits=word_bits, stride=stride)
    U = obs.from_rng(rng, samples=samples)
    profile = compute_profile(
        U,
        modulus=obs.modulus if modulus else None,
        bins=bins,
        max_subspace_dim=max_subspace_dim,
        branch_bins=branch_bins,
        branch_mode=branch_mode,
    )
    data = profile.as_dict()
    return {
        "H_rank": float(data["H_rank"]),
        "H_sub": float(data["H_sub"]),
        "H_branch": float(data["H_branch"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rngs", default="ondmax,system,lcg,xorshift,chacha20,quantum,masked,bounded")
    parser.add_argument("--samples", type=int, default=100000)
    parser.add_argument("--dimension", type=int, default=4)
    parser.add_argument("--word-bits", type=int, default=32)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--modulus", action="store_true")
    parser.add_argument("--bins", type=int, default=16)
    parser.add_argument("--max-subspace-dim", type=int, default=6)
    parser.add_argument("--branch-bins", type=int)
    parser.add_argument("--branch-mode", choices=["raw", "delta"], default="raw")
    parser.add_argument("--reference", default="data/benchmarks/reference_profiles.json")
    parser.add_argument("--seeds", default="1,2,3")
    parser.add_argument("--out-json", default="data/reports/evidence_report.json")
    parser.add_argument("--out-md", default="data/reports/evidence_report.md")
    args = parser.parse_args()

    rng_names = [r.strip() for r in args.rngs.split(",") if r.strip()]
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    ref = _load_reference(args.reference)

    results: List[Dict[str, Any]] = []
    for name in rng_names:
        seed_list = seeds if name in ("lcg", "xorshift", "chacha20", "quantum") else [None]
        for seed in seed_list:
            seed2 = (seed + 1) if seed is not None else None
            rng = _rng_from_name(name, seed=seed, seed2=seed2)
            metrics = _profile_metrics(
                rng=rng,
                samples=args.samples,
                dimension=args.dimension,
                word_bits=args.word_bits,
                stride=args.stride,
                modulus=args.modulus,
                bins=args.bins,
                max_subspace_dim=args.max_subspace_dim,
                branch_bins=args.branch_bins,
                branch_mode=args.branch_mode,
            )
            dist = ref.distance(metrics) if ref else None
            results.append(
                {
                    "rng": name,
                    "seed": seed,
                    "metrics": metrics,
                    "distance_to_class_I": dist,
                }
            )

    # Rank by distance to class I if available
    if ref:
        ranked = sorted(results, key=lambda r: float(r["distance_to_class_I"]))
        for i, row in enumerate(ranked, start=1):
            row["rank_class_I"] = i

    # Aggregate per RNG across seeds
    aggregates: Dict[str, Dict[str, Any]] = {}
    for row in results:
        name = row["rng"]
        aggregates.setdefault(name, {"metrics": [], "distances": []})
        aggregates[name]["metrics"].append(row["metrics"])
        if row.get("distance_to_class_I") is not None:
            aggregates[name]["distances"].append(float(row["distance_to_class_I"]))

    summary = []
    for name, data in aggregates.items():
        metrics_list = data["metrics"]
        mean_metrics = {
            "H_rank": float(np.mean([m["H_rank"] for m in metrics_list])),
            "H_sub": float(np.mean([m["H_sub"] for m in metrics_list])),
            "H_branch": float(np.mean([m["H_branch"] for m in metrics_list])),
        }
        std_metrics = {
            "H_rank": float(np.std([m["H_rank"] for m in metrics_list], ddof=0)),
            "H_sub": float(np.std([m["H_sub"] for m in metrics_list], ddof=0)),
            "H_branch": float(np.std([m["H_branch"] for m in metrics_list], ddof=0)),
        }
        dist_mean = float(np.mean(data["distances"])) if data["distances"] else None
        dist_std = float(np.std(data["distances"], ddof=0)) if data["distances"] else None
        summary.append(
            {
                "rng": name,
                "metrics_mean": mean_metrics,
                "metrics_std": std_metrics,
                "distance_to_class_I_mean": dist_mean,
                "distance_to_class_I_std": dist_std,
            }
        )

    payload = {
        "params": {
            "samples": args.samples,
            "dimension": args.dimension,
            "word_bits": args.word_bits,
            "stride": args.stride,
            "modulus": bool(args.modulus),
            "bins": args.bins,
            "max_subspace_dim": args.max_subspace_dim,
            "branch_bins": args.branch_bins,
            "branch_mode": args.branch_mode,
            "reference": args.reference,
        },
        "reference_class_I": asdict(ref) if ref else None,
        "results": results,
        "summary": summary,
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    # Markdown summary
    lines: List[str] = []
    lines.append("# Evidence Report — OND Metrics (Comparative)")
    lines.append("")
    lines.append("This report compares RNGs using OND metrics and distance to Class I reference.")
    lines.append("It is **not** a cryptographic proof and does not replace external batteries.")
    lines.append("")
    lines.append("## Parameters")
    for k, v in payload["params"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    if ref:
        lines.append("## Reference (Class I)")
        lines.append(f"- description: {ref.description}")
        lines.append(f"- mean: {ref.mean}")
        lines.append(f"- std: {ref.std}")
        lines.append("")

    lines.append("## Results (per seed)")
    lines.append("| rng | seed | H_rank | H_sub | H_branch | dist_to_class_I | rank |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in sorted(results, key=lambda r: float(r["distance_to_class_I"]) if r["distance_to_class_I"] is not None else 0.0):
        metrics = row["metrics"]
        dist = row.get("distance_to_class_I")
        rank = row.get("rank_class_I", "")
        dist_str = f"{dist:.6f}" if dist is not None else "NA"
        lines.append(
            f"| {row['rng']} | {row.get('seed', '')} | {metrics['H_rank']:.6f} | {metrics['H_sub']:.6f} | {metrics['H_branch']:.6f} | "
            f"{dist_str} | {rank} |"
        )

    lines.append("")
    lines.append("## Summary (mean ± std across seeds)")
    lines.append("| rng | H_rank μ | H_rank σ | H_sub μ | H_sub σ | H_branch μ | H_branch σ | dist μ | dist σ |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in sorted(summary, key=lambda r: float(r["distance_to_class_I_mean"]) if r["distance_to_class_I_mean"] is not None else 0.0):
        dist_mean = row["distance_to_class_I_mean"]
        dist_std = row["distance_to_class_I_std"]
        dist_mean_str = f"{dist_mean:.6f}" if dist_mean is not None else "NA"
        dist_std_str = f"{dist_std:.6f}" if dist_std is not None else "NA"
        lines.append(
            f"| {row['rng']} | {row['metrics_mean']['H_rank']:.6f} | {row['metrics_std']['H_rank']:.6f} | "
            f"{row['metrics_mean']['H_sub']:.6f} | {row['metrics_std']['H_sub']:.6f} | "
            f"{row['metrics_mean']['H_branch']:.6f} | {row['metrics_std']['H_branch']:.6f} | "
            f"{dist_mean_str} | {dist_std_str} |"
        )

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
