from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from ond_random.ond import ObservationMap, compute_profile
from ond_random.ond.calibration import calibrate_from_benchmark_dir
from ond_random.ond.objective import auto_weights_from_profiles, objective_from_profiles
from ond_random.ond.benchmark import ONDClass, ReferenceProfile, save_reference_profiles
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel


def parse_int_list(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--dimension", type=int, default=4)
    parser.add_argument("--word-bits", type=int, default=32)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--modulus", action="store_true")
    parser.add_argument("--seed-bytes", default="32,64,128")
    parser.add_argument("--reseed-intervals", default=str(1 << 20) + "," + str(1 << 22))
    parser.add_argument("--personalization", default="OND-RANDOM-v1")
    parser.add_argument("--benchmark-dir", default="data/benchmarks")
    parser.add_argument("--out", default="data/reports/ondmax_optimization.json")
    parser.add_argument("--stability-weight", type=float, default=1.0)
    parser.add_argument("--auto-weights", action="store_true")
    parser.add_argument("--update-references", action="store_true")
    args = parser.parse_args()

    seed_bytes_list = parse_int_list(args.seed_bytes)
    reseed_list = parse_int_list(args.reseed_intervals)

    obs = ObservationMap(dimension=args.dimension, word_bits=args.word_bits, stride=args.stride)
    target = calibrate_from_benchmark_dir(args.benchmark_dir)

    sources = {
        "os": SystemRNG(),
        "qrng": QuantumEmulatorRNG(seed=1, model=QuantumNoiseModel()),
        "emulator": QuantumEmulatorRNG(seed=2, model=QuantumNoiseModel(bias=0.05, drift_sigma=0.02, memory=0.2, phase_sigma=0.01)),
    }

    weights = None
    if args.auto_weights:
        baseline_profiles = {}
        baseline_rng = ONDMaxRNG(source=SystemRNG())
        for name, src in sources.items():
            rng = ONDMaxRNG(source=src)
            U = obs.from_rng(rng, samples=args.samples)
            profile = compute_profile(U, modulus=obs.modulus if args.modulus else None)
            baseline_profiles[name] = profile
        weights = auto_weights_from_profiles(baseline_profiles)

    results = []
    best = None
    best_system = None
    for seed_bytes, reseed in itertools.product(seed_bytes_list, reseed_list):
        profiles = {}
        system_U = None
        system_profile = None
        for name, src in sources.items():
            rng = ONDMaxRNG(
                source=src,
                seed_bytes=seed_bytes,
                reseed_interval=reseed,
                personalization=args.personalization.encode("utf-8"),
            )
            U = obs.from_rng(rng, samples=args.samples)
            profile = compute_profile(U, modulus=obs.modulus if args.modulus else None)
            profiles[name] = profile
            if name == "os":
                system_U = U
                system_profile = profile

        obj = objective_from_profiles(profiles, target=target, weights=weights, stability_weight=args.stability_weight)
        record = {
            "seed_bytes": seed_bytes,
            "reseed_interval": reseed,
            "profiles": {k: v.as_dict() for k, v in profiles.items()},
            "objective": obj.as_dict(),
        }
        results.append(record)
        if best is None or obj.score > best["objective"]["score"]:
            best = record
            best_system = (system_U, system_profile)

    # sort by highest score
    results.sort(key=lambda r: r["objective"]["score"], reverse=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")

    if args.update_references and best_system is not None:
        # overwrite I-ondmax with optimized profile (system source)
        U, profile = best_system
        bench = Path(args.benchmark_dir)
        bench.mkdir(parents=True, exist_ok=True)
        np_path = bench / "I-ondmax.npz"
        json_path = bench / "I-ondmax.json"
        profile_dict = profile.as_dict()
        profile_dict["ond_class"] = ONDClass.I.value
        profile_dict["id"] = "I-ondmax"
        np.savez_compressed(np_path, U=U)
        json_path.write_text(json.dumps(profile_dict, indent=2, sort_keys=True), encoding="utf-8")

        # rebuild reference_profiles.json from benchmark dir
        profiles_all = []
        for json_file in bench.glob("*.json"):
            if json_file.name == "reference_profiles.json":
                continue
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if "H_rank" in data:
                profiles_all.append(data)

        references = []
        for cls in ONDClass:
            subset = [p for p in profiles_all if p.get("ond_class") == cls.value]
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

        save_reference_profiles(str(bench / "reference_profiles.json"), references)


if __name__ == "__main__":
    main()
