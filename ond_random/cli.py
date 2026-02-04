from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from .ond import ObservationMap, compute_profile, OnlineCalibrator
from .ond.benchmark import classify_profile, load_reference_profiles, save_reference_profiles, ReferenceProfile, ONDClass
from .rng.base import RNG
from .rng.system import SystemRNG
from .rng.lcg import LCGRNG
from .rng.xorshift import XorShiftRNG
from .rng.chacha20 import ChaCha20RNG
from .rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from .rng.extractor import ONDMaxRNG
from .rng.structured import MaskedRNG, BoundedRNG
from .quantum.grover import grover_search
from .quantum.shor import shor_factor


def _load_calibration_bank(path: str) -> dict[str, OnlineCalibrator]:
    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "count" in data and "mean" in data:
        # Backward-compatibility: single calibrator state
        return {"default": OnlineCalibrator.from_state(data)}
    bank = {}
    for key, state in data.items():
        bank[key] = OnlineCalibrator.from_state(state)
    return bank


def _save_calibration_bank(path: str, bank: dict[str, OnlineCalibrator]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: v.state_dict() for k, v in bank.items()}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _calibration_key_from_args(args: argparse.Namespace) -> str:
    if getattr(args, "calibration_key", None):
        return args.calibration_key
    if args.rng in ("ondmax", "masked", "bounded") and args.source:
        return f"{args.rng}({args.source})"
    return args.rng


def _write_calibration_output(path: str, bank: dict[str, OnlineCalibrator], updated_key: str | list[str] | None = None) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    targets = {}
    for key, cal in bank.items():
        target = cal.target(description="online")
        targets[key] = {
            "count": cal.count,
            "mean": target.mean,
            "std": target.std,
            "description": target.description,
        }
    payload = {
        "updated_key": updated_key,
        "targets": targets,
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _rng_from_args(args: argparse.Namespace) -> RNG:
    name = args.rng
    if name == "system":
        return SystemRNG()
    if name == "lcg":
        seed = args.seed if args.seed is not None else 1
        return LCGRNG(seed=seed)
    if name == "xorshift":
        s1 = args.seed if args.seed is not None else 1
        s2 = args.seed2 if args.seed2 is not None else 2
        return XorShiftRNG(seed1=s1, seed2=s2)
    if name == "chacha20":
        if args.key_hex:
            key = bytes.fromhex(args.key_hex)
            return ChaCha20RNG(key=key)
        seed = args.seed if args.seed is not None else 1
        return ChaCha20RNG.from_seed(seed.to_bytes(8, "big"))
    if name == "quantum":
        model = QuantumNoiseModel(
            bias=args.bias,
            drift_sigma=args.drift_sigma,
            drift_rho=args.drift_rho,
            memory=args.memory,
            phase_sigma=args.phase_sigma,
        )
        return QuantumEmulatorRNG(seed=args.seed, model=model)
    if name == "ondmax":
        source = _rng_from_args(argparse.Namespace(**{**vars(args), "rng": args.source})) if args.source else SystemRNG()
        return ONDMaxRNG(source=source)
    if name == "masked":
        source = _rng_from_args(argparse.Namespace(**{**vars(args), "rng": args.source})) if args.source else SystemRNG()
        return MaskedRNG(source=source, mask_low_bits=args.mask_low_bits)
    if name == "bounded":
        source = _rng_from_args(argparse.Namespace(**{**vars(args), "rng": args.source})) if args.source else SystemRNG()
        return BoundedRNG(source=source, bound_bits=args.bound_bits)
    raise ValueError(f"unknown rng: {name}")


def cmd_gen(args: argparse.Namespace) -> None:
    rng = _rng_from_args(args)
    if args.bits is not None:
        data = rng.random_bits(args.bits)
    else:
        data = rng.random_bytes(args.bytes)
    if args.out:
        Path(args.out).write_bytes(data)
    else:
        if args.hex:
            print(data.hex())
        else:
            os.write(1, data)


def cmd_profile(args: argparse.Namespace) -> None:
    rng = _rng_from_args(args)
    obs = ObservationMap(dimension=args.dimension, word_bits=args.word_bits, stride=args.stride)
    U = obs.from_rng(rng, samples=args.samples)
    profile = compute_profile(
        U,
        modulus=obs.modulus if args.modulus else None,
        bins=args.bins,
        max_subspace_dim=args.max_subspace_dim,
        branch_bins=args.branch_bins,
        branch_mode=args.branch_mode,
    )
    result = profile.as_dict()
    # Optional classification
    if args.references:
        refs = load_reference_profiles(args.references)
        result["ond_class"] = classify_profile(result, refs).value
    if args.auto_calibrate:
        bank = _load_calibration_bank(args.calibration_state)
        key = _calibration_key_from_args(args)
        calibrator = bank.get(key, OnlineCalibrator())
        calibrator.update(result)
        bank[key] = calibrator
        _save_calibration_bank(args.calibration_state, bank)
        _write_calibration_output(args.calibration_out, bank, updated_key=key)

    output = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


def cmd_benchmark(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    obs = ObservationMap(dimension=args.dimension, word_bits=args.word_bits, stride=args.stride)

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
        U = obs.from_rng(rng, samples=args.samples)
        profile = compute_profile(
            U,
            modulus=obs.modulus if args.modulus else None,
            bins=args.bins,
            max_subspace_dim=args.max_subspace_dim,
            branch_bins=args.branch_bins,
            branch_mode=args.branch_mode,
        )
        profile_dict = profile.as_dict()
        profile_dict["ond_class"] = cls.value
        profile_dict["id"] = name
        profiles.append(profile_dict)
        np.savez_compressed(out_dir / f"{name}.npz", U=U)
        (out_dir / f"{name}.json").write_text(json.dumps(profile_dict, indent=2, sort_keys=True), encoding="utf-8")

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

    if args.auto_calibrate:
        bank = _load_calibration_bank(args.calibration_state)
        filtered = profiles
        if args.calibration_class:
            filtered = [p for p in profiles if p.get("ond_class") == args.calibration_class]
        updated_keys = []
        for p in filtered:
            if args.calibration_group == "ond_class":
                key = f"class:{p.get('ond_class', 'unknown')}"
            elif args.calibration_group == "all":
                key = "all"
            else:
                key = p.get("id", "unknown")
            calibrator = bank.get(key, OnlineCalibrator())
            calibrator.update(p)
            bank[key] = calibrator
            updated_keys.append(key)
        _save_calibration_bank(args.calibration_state, bank)
        _write_calibration_output(args.calibration_out, bank, updated_key=sorted(set(updated_keys)))

    if args.out_report:
        (Path(args.out_report)).write_text(json.dumps(profiles, indent=2, sort_keys=True), encoding="utf-8")
    else:
        print(json.dumps(profiles, indent=2, sort_keys=True))


def cmd_grover(args: argparse.Namespace) -> None:
    if args.targets:
        targets = [int(x.strip()) for x in args.targets.split(",") if x.strip()]
    elif args.n_solutions is not None:
        if args.n_solutions <= 0:
            raise ValueError("n_solutions must be positive")
        if args.n_solutions >= args.items:
            raise ValueError("n_solutions must be < items")
        step = max(1, args.items // args.n_solutions)
        targets = [i * step for i in range(args.n_solutions)]
    elif args.targets_random is not None:
        if args.targets_random <= 0:
            raise ValueError("targets_random must be positive")
        if args.targets_random >= args.items:
            raise ValueError("targets_random must be < items")
        rng = ONDMaxRNG(SystemRNG())
        chosen = set()
        while len(chosen) < args.targets_random:
            chosen.add(rng.random_uint(args.items))
        targets = sorted(chosen)
    else:
        targets = None
    result = grover_search(
        target=args.target,
        targets=targets,
        n_items=args.items,
        iterations=args.iterations,
        shots=args.shots,
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))


def cmd_shor(args: argparse.Namespace) -> None:
    result = shor_factor(N=args.N, a=args.a, shots=args.shots, gamma1=args.gamma1, gamma_phi=args.gamma_phi)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))


def cmd_shor_batch(args: argparse.Namespace) -> None:
    results = []
    for N in (15, 21, 35):
        res = shor_factor(N=N, a=args.a, shots=args.shots, gamma1=args.gamma1, gamma_phi=args.gamma_phi)
        results.append(res.as_dict())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ond-random", description="OND Random system")
    sub = parser.add_subparsers(dest="command", required=True)

    common_rng = argparse.ArgumentParser(add_help=False)
    common_rng.add_argument("--rng", choices=["system", "lcg", "xorshift", "chacha20", "quantum", "ondmax", "masked", "bounded"], default="system")
    common_rng.add_argument("--seed", type=int)
    common_rng.add_argument("--seed2", type=int)
    common_rng.add_argument("--key-hex", dest="key_hex")
    common_rng.add_argument("--source", choices=["system", "lcg", "xorshift", "chacha20", "quantum"], default="system")
    common_rng.add_argument("--bias", type=float, default=0.0)
    common_rng.add_argument("--drift-sigma", type=float, default=1e-3)
    common_rng.add_argument("--drift-rho", type=float, default=0.999)
    common_rng.add_argument("--memory", type=float, default=0.0)
    common_rng.add_argument("--phase-sigma", type=float, default=0.0)
    common_rng.add_argument("--mask-low-bits", type=int, default=4)
    common_rng.add_argument("--bound-bits", type=int, default=12)

    p_gen = sub.add_parser("gen", parents=[common_rng], help="Generate random bytes")
    p_gen.add_argument("--bytes", type=int, default=64)
    p_gen.add_argument("--bits", type=int, help="Exact bit length (e.g., 256, 512, 1024)")
    p_gen.add_argument("--out")
    p_gen.add_argument("--hex", action="store_true")
    p_gen.set_defaults(func=cmd_gen)

    p_profile = sub.add_parser("profile", parents=[common_rng], help="Compute OND profile")
    p_profile.add_argument("--samples", type=int, default=10000)
    p_profile.add_argument("--dimension", type=int, default=4)
    p_profile.add_argument("--word-bits", type=int, default=32)
    p_profile.add_argument("--stride", type=int, default=1)
    p_profile.add_argument("--modulus", action="store_true", help="Use modulus wrapping")
    p_profile.add_argument("--bins", type=int, default=16)
    p_profile.add_argument("--max-subspace-dim", type=int, default=6)
    p_profile.add_argument("--branch-bins", type=int, default=None)
    p_profile.add_argument("--branch-mode", choices=["raw", "delta"], default="raw")
    p_profile.add_argument("--references")
    p_profile.add_argument("--out")
    p_profile.add_argument("--auto-calibrate", action="store_true")
    p_profile.add_argument("--calibration-state", default="data/reports/online_calibration_state.json")
    p_profile.add_argument("--calibration-out", default="data/reports/auto_calibration.json")
    p_profile.add_argument("--calibration-key", help="override calibration key (default: rng or rng(source))")
    p_profile.set_defaults(func=cmd_profile)

    p_bench = sub.add_parser("benchmark", help="Generate benchmark datasets and profiles")
    p_bench.add_argument("--out-dir", default="data/benchmarks")
    p_bench.add_argument("--out-report")
    p_bench.add_argument("--samples", type=int, default=10000)
    p_bench.add_argument("--dimension", type=int, default=4)
    p_bench.add_argument("--word-bits", type=int, default=32)
    p_bench.add_argument("--stride", type=int, default=1)
    p_bench.add_argument("--modulus", action="store_true", help="Use modulus wrapping")
    p_bench.add_argument("--bins", type=int, default=16)
    p_bench.add_argument("--max-subspace-dim", type=int, default=6)
    p_bench.add_argument("--branch-bins", type=int, default=None)
    p_bench.add_argument("--branch-mode", choices=["raw", "delta"], default="raw")
    p_bench.add_argument("--auto-calibrate", action="store_true")
    p_bench.add_argument("--calibration-state", default="data/reports/online_calibration_state.json")
    p_bench.add_argument("--calibration-out", default="data/reports/auto_calibration.json")
    p_bench.add_argument("--calibration-class", choices=[c.value for c in ONDClass])
    p_bench.add_argument("--calibration-group", choices=["id", "ond_class", "all"], default="id")
    p_bench.set_defaults(func=cmd_benchmark)

    p_grover = sub.add_parser("grover", help="Run Grover search (statevector)")
    p_grover.add_argument("--items", type=int, required=True, help="number of items (e.g., 100000)")
    p_grover.add_argument("--target", type=int, help="single target index")
    p_grover.add_argument("--targets", help="comma-separated list of target indices")
    p_grover.add_argument("--n-solutions", type=int, help="auto-generate this many targets")
    p_grover.add_argument("--targets-random", type=int, help="randomly choose this many targets")
    p_grover.add_argument("--iterations", type=int, help="override iterations")
    p_grover.add_argument("--shots", type=int, default=100, help="measurement shots")
    p_grover.set_defaults(func=cmd_grover)

    p_shor = sub.add_parser("shor", help="Run Shor factorization (ideal period finding)")
    p_shor.add_argument("--N", type=int, required=True, help="composite integer to factor")
    p_shor.add_argument("--a", type=int, required=True, help="base a (coprime to N)")
    p_shor.add_argument("--shots", type=int, default=20)
    p_shor.add_argument("--gamma1", type=float, help="noise gamma1 (amplitude damping)")
    p_shor.add_argument("--gamma-phi", dest="gamma_phi", type=float, help="noise gamma_phi (dephasing)")
    p_shor.set_defaults(func=cmd_shor)

    p_shor_batch = sub.add_parser("shor-batch", help="Run Shor for N=15,21,35 and save report")
    p_shor_batch.add_argument("--a", type=int, default=2)
    p_shor_batch.add_argument("--shots", type=int, default=200)
    p_shor_batch.add_argument("--gamma1", type=float)
    p_shor_batch.add_argument("--gamma-phi", dest="gamma_phi", type=float)
    p_shor_batch.add_argument("--out", default="data/reports/shor_batch.json")
    p_shor_batch.set_defaults(func=cmd_shor_batch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
