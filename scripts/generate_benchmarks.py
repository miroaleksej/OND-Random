from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ond_random.ond import ObservationMap, compute_profile
from ond_random.ond.benchmark import ONDClass, ReferenceProfile, save_reference_profiles
from ond_random.rng.system import SystemRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.structured import MaskedRNG, BoundedRNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel


def generate(out_dir: Path, samples: int, dimension: int, word_bits: int, modulus: bool, stride: int) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    obs = ObservationMap(dimension=dimension, word_bits=word_bits, stride=stride)

    rng_specs = [
        ("I-ondmax", ONDMaxRNG(SystemRNG()), ONDClass.I),
        ("II-lcg", LCGRNG(seed=1), ONDClass.II),
        ("II-xorshift", XorShiftRNG(1, 2), ONDClass.II),
        ("III-bounded", BoundedRNG(SystemRNG(), bound_bits=12), ONDClass.III),
        ("IV-masked", MaskedRNG(SystemRNG(), mask_low_bits=6), ONDClass.IV),
        ("Q-ideal", QuantumEmulatorRNG(seed=1, model=QuantumNoiseModel()), ONDClass.I),
        ("Q-drift", QuantumEmulatorRNG(seed=2, model=QuantumNoiseModel(bias=0.05, drift_sigma=0.02, memory=0.2, phase_sigma=0.01)), ONDClass.III),
    ]

    profiles = []
    for name, rng, cls in rng_specs:
        U = obs.from_rng(rng, samples=samples)
        profile = compute_profile(U, modulus=obs.modulus if modulus else None, branch_bins=None)
        data = profile.as_dict()
        data["ond_class"] = cls.value
        data["id"] = name
        profiles.append(data)
        np.savez_compressed(out_dir / f"{name}.npz", U=U)
        (out_dir / f"{name}.json").write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    # Build reference profiles
    references = []
    for cls in ONDClass:
        subset = [p for p in profiles if p["ond_class"] == cls.value]
        if not subset:
            continue
        mean = {
            "H_rank": float(np.mean([p["H_rank"] for p in subset])),
            "H_sub": float(np.mean([p["H_sub"] for p in subset])),
            "H_branch": float(np.mean([p["H_branch"] for p in subset])),
        }
        std = {
            "H_rank": float(np.std([p["H_rank"] for p in subset], ddof=1) if len(subset) > 1 else 0.05),
            "H_sub": float(np.std([p["H_sub"] for p in subset], ddof=1) if len(subset) > 1 else 0.05),
            "H_branch": float(np.std([p["H_branch"] for p in subset], ddof=1) if len(subset) > 1 else 0.05),
        }
        references.append(ReferenceProfile(ond_class=cls, mean=mean, std=std, description=f"auto-{cls.value}"))
    save_reference_profiles(str(out_dir / "reference_profiles.json"), references)

    return profiles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/benchmarks")
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--dimension", type=int, default=4)
    parser.add_argument("--word-bits", type=int, default=32)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--modulus", action="store_true")
    parser.add_argument("--report", default="data/reports/benchmark_profiles.json")
    args = parser.parse_args()

    profiles = generate(Path(args.out_dir), args.samples, args.dimension, args.word_bits, args.modulus, args.stride)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(profiles, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
