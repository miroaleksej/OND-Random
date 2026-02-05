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


def _rng_from_name(name: str) -> RNG:
    if name == "system":
        return SystemRNG()
    if name == "lcg":
        return LCGRNG(seed=1)
    if name == "xorshift":
        return XorShiftRNG(seed1=1, seed2=2)
    if name == "chacha20":
        return ChaCha20RNG.from_seed((1).to_bytes(8, "big"))
    if name == "quantum":
        return QuantumEmulatorRNG(seed=1, model=QuantumNoiseModel())
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
    parser.add_argument("--out-json", default="data/reports/evidence_report.json")
    parser.add_argument("--out-md", default="data/reports/evidence_report.md")
    args = parser.parse_args()

    rng_names = [r.strip() for r in args.rngs.split(",") if r.strip()]
    ref = _load_reference(args.reference)

    results: List[Dict[str, Any]] = []
    for name in rng_names:
        rng = _rng_from_name(name)
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
                "metrics": metrics,
                "distance_to_class_I": dist,
            }
        )

    # Rank by distance to class I if available
    if ref:
        ranked = sorted(results, key=lambda r: float(r["distance_to_class_I"]))
        for i, row in enumerate(ranked, start=1):
            row["rank_class_I"] = i

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

    lines.append("## Results")
    lines.append("| rng | H_rank | H_sub | H_branch | dist_to_class_I | rank |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for row in sorted(results, key=lambda r: float(r["distance_to_class_I"]) if r["distance_to_class_I"] is not None else 0.0):
        metrics = row["metrics"]
        dist = row.get("distance_to_class_I")
        rank = row.get("rank_class_I", "")
        dist_str = f"{dist:.6f}" if dist is not None else "NA"
        lines.append(
            f"| {row['rng']} | {metrics['H_rank']:.6f} | {metrics['H_sub']:.6f} | {metrics['H_branch']:.6f} | "
            f"{dist_str} | {rank} |"
        )

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
