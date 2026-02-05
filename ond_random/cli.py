from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .ond import (
    ObservationMap,
    ObservationsMeta,
    OnlineCalibrator,
    compute_profile,
    delay_embed_series,
    load_csv_matrix,
    load_csv_series,
    load_ecdsa_rsz_csv,
    load_npy,
    load_npz,
    load_text_series_regex,
    read_observations_jsonl,
    torus_embed_modular,
    unit_scale_modular,
    write_observations_jsonl,
    add_entry,
    check_entry,
    load_registry,
    save_registry,
)
from .ond.benchmark import classify_profile, load_reference_profiles, save_reference_profiles, ReferenceProfile, ONDClass
from .ond.baseline_policy import load_policy, select_policy
from .ond.odd_report import build_ond_art_report, hash_json, hash_text
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


def _parse_int_base0(text: str) -> int:
    return int(text, 0)


def _load_json_arg(value: str | None) -> dict | None:
    if not value:
        return None
    if value.startswith("@"):
        payload = Path(value[1:]).read_text(encoding="utf-8")
        return json.loads(payload)
    return json.loads(value)


def _load_text_arg(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


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


def _infer_input_format(path: str, explicit: str | None) -> str:
    if explicit and explicit != "auto":
        return explicit
    suffix = Path(path).suffix.lower()
    if suffix == ".npy":
        return "npy"
    if suffix == ".npz":
        return "npz"
    if suffix == ".csv":
        return "csv"
    return "text"


def _split_columns(text: str | None) -> list[str]:
    if not text:
        return []
    return [c.strip() for c in text.split(",") if c.strip()]


def _load_U_from_file_args(args: argparse.Namespace) -> tuple[np.ndarray, int | None]:
    fmt = _infer_input_format(args.input, args.input_format)
    delimiter = args.delimiter

    modulus: int | None = args.modulus
    is_series = False

    if fmt == "npy":
        U_raw = load_npy(args.input)
        if U_raw.ndim == 1:
            is_series = True
    elif fmt == "npz":
        U_raw = load_npz(args.input, key=args.npz_key)
        if U_raw.ndim == 1:
            is_series = True
    elif fmt == "csv":
        if args.ecdsa_rsz:
            if args.ecdsa_n is None:
                raise ValueError("--ecdsa-n is required when --ecdsa-rsz is set")
            modulus = int(args.ecdsa_n)
            U_raw = load_ecdsa_rsz_csv(
                args.input,
                n=modulus,
                r_col=args.ecdsa_r_col,
                s_col=args.ecdsa_s_col,
                z_col=args.ecdsa_z_col,
                delimiter=delimiter,
            )
        elif args.column:
            is_series = True
            U_raw = load_csv_series(args.input, column=args.column, delimiter=delimiter)
        else:
            columns = _split_columns(args.columns)
            if not columns:
                raise ValueError("CSV input requires --columns (matrix) or --column (series), or --ecdsa-rsz")
            U_raw = load_csv_matrix(args.input, columns=columns, delimiter=delimiter)
    elif fmt == "text":
        if not args.regex:
            raise ValueError("text input requires --regex")
        is_series = True
        U_raw = load_text_series_regex(args.input, pattern=args.regex)
    else:
        raise ValueError(f"unsupported input format: {fmt}")

    # Build 2D observation matrix U
    if is_series:
        series = np.asarray(U_raw, dtype=float).reshape(-1)
        if args.embed_dim > 1:
            U = delay_embed_series(series, embed_dim=args.embed_dim, delay=args.embed_delay, stride=args.embed_stride)
        else:
            U = series.reshape(-1, 1)
        effective_modulus = None
    else:
        U = np.asarray(U_raw)
        effective_modulus = modulus

    # Optional modular embedding
    if effective_modulus is not None:
        if args.modulus_embedding == "unit":
            U = unit_scale_modular(U, effective_modulus)
            effective_modulus = None
        elif args.modulus_embedding == "torus":
            U = torus_embed_modular(U, effective_modulus)
            effective_modulus = None
        elif args.modulus_embedding != "wrap":
            raise ValueError("modulus_embedding must be wrap|unit|torus")

    return U, effective_modulus


def cmd_profile_file(args: argparse.Namespace) -> None:
    U, effective_modulus = _load_U_from_file_args(args)

    profile = compute_profile(
        U,
        modulus=effective_modulus,
        bins=args.bins,
        max_subspace_dim=args.max_subspace_dim,
        branch_bins=args.branch_bins,
        branch_mode=args.branch_mode,
    )
    result = profile.as_dict()
    if args.references:
        refs = load_reference_profiles(args.references)
        result["ond_class"] = classify_profile(result, refs).value

    output = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


def cmd_obs_export(args: argparse.Namespace) -> None:
    U, effective_modulus = _load_U_from_file_args(args)

    if not args.pi_id or not args.pi_version:
        raise ValueError("--pi-id and --pi-version are required for obs-export")

    obs_space: dict[str, Any]
    if args.obs_space_type:
        obs_space = {"type": args.obs_space_type}
        if args.obs_space_d:
            obs_space["d"] = int(args.obs_space_d)
        if args.obs_space_modulus:
            obs_space["modulus"] = int(args.obs_space_modulus)
    else:
        if effective_modulus is not None:
            obs_space = {"type": "Z_mod_m", "modulus": int(effective_modulus), "d": int(U.shape[1])}
        else:
            obs_space = {"type": "R^d", "d": int(U.shape[1])}

    pi_spec_raw = _load_text_arg(args.pi_spec)
    if pi_spec_raw:
        try:
            pi_spec = json.loads(pi_spec_raw)
            pi_spec_hash = hash_json(pi_spec)
        except Exception:
            pi_spec_hash = hash_text(pi_spec_raw)
    else:
        pi_spec_hash = hash_json({"pi_id": args.pi_id, "pi_version": args.pi_version, "obs_space": obs_space})

    context = _load_json_arg(args.context_json)

    meta = ObservationsMeta(
        pi_id=args.pi_id,
        pi_version=args.pi_version,
        pi_spec_hash=pi_spec_hash,
        obs_space=obs_space,
        spec={"name": "ODD-OBS", "version": "0.1"},
        context=context,
        public_context_hash=args.public_context_hash,
    )

    if args.pi_registry:
        registry = load_registry(args.pi_registry)
        if args.pi_registry_mode == "check":
            check_entry(registry, pi_id=args.pi_id, pi_version=args.pi_version, pi_spec_hash=pi_spec_hash)
        elif args.pi_registry_mode == "add":
            add_entry(
                registry,
                pi_id=args.pi_id,
                pi_version=args.pi_version,
                pi_spec_hash=pi_spec_hash,
                obs_space=obs_space,
                description=args.pi_description,
            )
            save_registry(args.pi_registry, registry)
        else:
            raise ValueError("pi_registry_mode must be 'check' or 'add'")

    write_observations_jsonl(args.out, U, meta, stringify_large_ints=not args.no_stringify_large_ints)


def cmd_odd_report(args: argparse.Namespace) -> None:
    baseline_report = None
    if args.baseline_report:
        baseline_report = json.loads(Path(args.baseline_report).read_text(encoding="utf-8"))

    params = _load_json_arg(args.params_json) or {}

    if args.public_context_hash:
        public_context_hash = args.public_context_hash
    elif args.public_context:
        public_context_hash = hash_text(_load_text_arg(args.public_context) or "")
    else:
        public_context_hash = None

    percentiles = None
    profile = args.profile
    if args.baseline_policy:
        policy = load_policy(args.baseline_policy)
        policy_pct, policy_profile = select_policy(policy, args.protocol, args.scheme)
        if percentiles is None:
            percentiles = policy_pct
        if profile is None:
            profile = policy_profile
    if args.baseline_percentiles:
        parsed = tuple(float(x) for x in args.baseline_percentiles.split(","))
        if len(parsed) != 3:
            raise ValueError("--baseline-percentiles must have 3 comma-separated values")
        percentiles = parsed
    if percentiles is None:
        percentiles = (50.0, 80.0, 95.0)
    if profile is None:
        profile = "core"

    notes = []
    if args.note:
        notes.extend(args.note)
    if not any("Diagnostic only; no security claim." in n for n in notes):
        notes.append("Diagnostic only; no security claim.")

    try:
        from ond_random import __version__ as pkg_version
    except Exception:
        pkg_version = "unknown"
    method_version = args.method_version or f"ond-random@{pkg_version}/odd-report"

    report = build_ond_art_report(
        observations_path=args.observations,
        baseline_observations=args.baseline_observations,
        baseline_report=baseline_report,
        baseline_id=args.baseline_id,
        baseline_percentiles=(percentiles[0], percentiles[1], percentiles[2]),
        bins=args.bins,
        max_subspace_dim=args.max_subspace_dim,
        branch_bins=args.branch_bins,
        branch_mode=args.branch_mode,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        protocol=args.protocol,
        scheme=args.scheme,
        params=params,
        public_context_hash=public_context_hash,
        order=args.order,
        message_policy=args.message_policy,
        spec_profile=profile,
        method_version=method_version,
        notes=notes,
        timezone_name=args.timezone,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


def cmd_pi_registry(args: argparse.Namespace) -> None:
    registry = load_registry(args.registry)
    if args.pi_command == "add":
        pi_spec_raw = _load_text_arg(args.pi_spec) or ""
        try:
            pi_spec = json.loads(pi_spec_raw)
            pi_spec_hash = hash_json(pi_spec)
        except Exception:
            pi_spec_hash = hash_text(pi_spec_raw)

        obs_space = {"type": args.obs_space_type}
        if args.obs_space_d is not None:
            obs_space["d"] = int(args.obs_space_d)
        if args.obs_space_modulus is not None:
            obs_space["modulus"] = int(args.obs_space_modulus)

        add_entry(
            registry,
            pi_id=args.pi_id,
            pi_version=args.pi_version,
            pi_spec_hash=pi_spec_hash,
            obs_space=obs_space,
            description=args.description,
        )
        save_registry(args.registry, registry)
        print(json.dumps(registry, indent=2, sort_keys=True))
    elif args.pi_command == "check":
        pi_spec_raw = _load_text_arg(args.pi_spec) or ""
        try:
            pi_spec = json.loads(pi_spec_raw)
            pi_spec_hash = hash_json(pi_spec)
        except Exception:
            pi_spec_hash = hash_text(pi_spec_raw)
        check_entry(registry, pi_id=args.pi_id, pi_version=args.pi_version, pi_spec_hash=pi_spec_hash)
        print("OK")
    else:
        raise ValueError("Unknown pi-registry command")
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

    p_profile_file = sub.add_parser("profile-file", help="Compute OND profile from a file (CSV/NPY/log)")
    p_profile_file.add_argument("--input", required=True, help="Input file path")
    p_profile_file.add_argument("--input-format", choices=["auto", "npy", "npz", "csv", "text"], default="auto")
    p_profile_file.add_argument("--npz-key", default="U")
    p_profile_file.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    p_profile_file.add_argument("--columns", help="CSV matrix columns (comma-separated)")
    p_profile_file.add_argument("--column", help="CSV scalar column (for series)")
    p_profile_file.add_argument("--regex", help="Regex with one capture group (for text series)")
    p_profile_file.add_argument("--embed-dim", type=int, default=1, help="Delay embedding dimension for series (default: 1)")
    p_profile_file.add_argument("--embed-delay", type=int, default=1, help="Delay embedding delay (default: 1)")
    p_profile_file.add_argument("--embed-stride", type=int, default=1, help="Delay embedding stride (default: 1)")
    p_profile_file.add_argument("--modulus", type=_parse_int_base0, default=None, help="Optional modulus for modular observations (supports 0x... hex)")
    p_profile_file.add_argument("--modulus-embedding", choices=["wrap", "unit", "torus"], default="wrap")
    p_profile_file.add_argument("--ecdsa-rsz", action="store_true", help="Parse CSV r,s,z and map to (u_r,u_z)")
    p_profile_file.add_argument("--ecdsa-n", type=_parse_int_base0, default=None, help="ECDSA group order n (required with --ecdsa-rsz; supports 0x... hex)")
    p_profile_file.add_argument("--ecdsa-r-col", default="r")
    p_profile_file.add_argument("--ecdsa-s-col", default="s")
    p_profile_file.add_argument("--ecdsa-z-col", default="z")
    p_profile_file.add_argument("--bins", type=int, default=16)
    p_profile_file.add_argument("--max-subspace-dim", type=int, default=6)
    p_profile_file.add_argument("--branch-bins", type=int, default=None)
    p_profile_file.add_argument("--branch-mode", choices=["raw", "delta"], default="raw")
    p_profile_file.add_argument("--references")
    p_profile_file.add_argument("--out")
    p_profile_file.set_defaults(func=cmd_profile_file)

    p_obs = sub.add_parser("obs-export", help="Export observations.jsonl with pi_id/pi_version")
    p_obs.add_argument("--input", required=True, help="Input file path")
    p_obs.add_argument("--input-format", choices=["auto", "npy", "npz", "csv", "text"], default="auto")
    p_obs.add_argument("--npz-key", default="U")
    p_obs.add_argument("--delimiter", default=",")
    p_obs.add_argument("--columns", help="CSV matrix columns (comma-separated)")
    p_obs.add_argument("--column", help="CSV scalar column (for series)")
    p_obs.add_argument("--regex", help="Regex with one capture group (for text series)")
    p_obs.add_argument("--embed-dim", type=int, default=1)
    p_obs.add_argument("--embed-delay", type=int, default=1)
    p_obs.add_argument("--embed-stride", type=int, default=1)
    p_obs.add_argument("--modulus", type=_parse_int_base0, default=None)
    p_obs.add_argument("--modulus-embedding", choices=["wrap", "unit", "torus"], default="wrap")
    p_obs.add_argument("--ecdsa-rsz", action="store_true")
    p_obs.add_argument("--ecdsa-n", type=_parse_int_base0, default=None)
    p_obs.add_argument("--ecdsa-r-col", default="r")
    p_obs.add_argument("--ecdsa-s-col", default="s")
    p_obs.add_argument("--ecdsa-z-col", default="z")
    p_obs.add_argument("--pi-id", required=True)
    p_obs.add_argument("--pi-version", required=True)
    p_obs.add_argument("--pi-spec", help="PI spec as JSON/text or @file path")
    p_obs.add_argument("--pi-registry", help="Optional registry JSON path")
    p_obs.add_argument("--pi-registry-mode", choices=["check", "add"], default="check")
    p_obs.add_argument("--pi-description", help="Optional description for registry entry")
    p_obs.add_argument("--obs-space-type", help="Override obs_space.type (e.g., R^d, Z_mod_m)")
    p_obs.add_argument("--obs-space-d", type=int, default=None)
    p_obs.add_argument("--obs-space-modulus", type=_parse_int_base0, default=None)
    p_obs.add_argument("--context-json", help="Optional context JSON or @file")
    p_obs.add_argument("--public-context-hash", help="Optional public_context_hash to embed")
    p_obs.add_argument("--no-stringify-large-ints", action="store_true")
    p_obs.add_argument("--out", required=True, help="Output observations.jsonl path")
    p_obs.set_defaults(func=cmd_obs_export)

    p_odd = sub.add_parser("odd-report", help="Generate OND-ART report from observations.jsonl")
    p_odd.add_argument("--observations", required=True, help="observations.jsonl path")
    p_odd.add_argument("--out", required=True, help="Report output path")
    p_odd.add_argument("--protocol", default="custom")
    p_odd.add_argument("--scheme", default="custom")
    p_odd.add_argument("--params-json", help="JSON params or @file")
    p_odd.add_argument("--public-context", help="Text or @file to hash as public_context_hash")
    p_odd.add_argument("--public-context-hash", help="Explicit public_context_hash")
    p_odd.add_argument("--order", choices=["time", "generation_index", "custom"], default="custom")
    p_odd.add_argument("--message-policy", default="custom")
    p_odd.add_argument("--profile", choices=["core", "recommended", "dev"], default=None)
    p_odd.add_argument("--method-version", help="Override method_version in report")
    p_odd.add_argument("--timezone", default="Etc/UTC")
    p_odd.add_argument("--bins", type=int, default=16)
    p_odd.add_argument("--max-subspace-dim", type=int, default=6)
    p_odd.add_argument("--branch-bins", type=int, default=None)
    p_odd.add_argument("--branch-mode", choices=["raw", "delta"], default="raw")
    p_odd.add_argument("--bootstrap-samples", type=int, default=200)
    p_odd.add_argument("--bootstrap-seed", type=int, default=0)
    p_odd.add_argument("--baseline-observations", help="Baseline observations.jsonl path")
    p_odd.add_argument("--baseline-report", help="Baseline report JSON path")
    p_odd.add_argument("--baseline-id", default="baseline-1")
    p_odd.add_argument("--baseline-policy", help="Baseline policy JSON path")
    p_odd.add_argument("--baseline-percentiles", default=None)
    p_odd.add_argument("--note", action="append")
    p_odd.set_defaults(func=cmd_odd_report)

    p_pi = sub.add_parser("pi-registry", help="Manage pi_id registry")
    pi_sub = p_pi.add_subparsers(dest="pi_command", required=True)

    p_pi_add = pi_sub.add_parser("add", help="Add entry to registry")
    p_pi_add.add_argument("--registry", required=True)
    p_pi_add.add_argument("--pi-id", required=True)
    p_pi_add.add_argument("--pi-version", required=True)
    p_pi_add.add_argument("--pi-spec", required=True, help="PI spec JSON/text or @file")
    p_pi_add.add_argument("--obs-space-type", required=True)
    p_pi_add.add_argument("--obs-space-d", type=int, default=None)
    p_pi_add.add_argument("--obs-space-modulus", type=_parse_int_base0, default=None)
    p_pi_add.add_argument("--description")
    p_pi_add.set_defaults(func=cmd_pi_registry)

    p_pi_check = pi_sub.add_parser("check", help="Check registry entry")
    p_pi_check.add_argument("--registry", required=True)
    p_pi_check.add_argument("--pi-id", required=True)
    p_pi_check.add_argument("--pi-version", required=True)
    p_pi_check.add_argument("--pi-spec", required=True, help="PI spec JSON/text or @file")
    p_pi_check.set_defaults(func=cmd_pi_registry)


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
