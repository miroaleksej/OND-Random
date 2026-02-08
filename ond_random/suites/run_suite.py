from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from ond_random.ond import ObservationMap, ObservationsMeta, write_observations_jsonl
from ond_random.ond.baseline_policy import load_policy, select_policy
from ond_random.ond.odd_report import build_ond_art_report, hash_json, hash_text
from ond_random.rng.base import RNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from ond_random.rng.structured import BoundedRNG, MaskedRNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.xorshift import XorShiftRNG


def _parse_suite_list(value: str | None) -> List[str]:
    allowed = {"ond", "nist", "practrand", "testu01", "ea90b"}
    if not value or value.strip().lower() == "all":
        return sorted(allowed)
    raw = [item.strip().lower() for item in value.split(",")]
    suites = [item for item in raw if item]
    unknown = [item for item in suites if item not in allowed]
    if unknown:
        raise ValueError(f"unknown suites: {', '.join(sorted(set(unknown)))}")
    return suites


def _mode_defaults(mode: str) -> Dict[str, int]:
    if mode == "full":
        return {
            "ond_samples": 100_000,
            "nist_bits": 10_000_000,
            "practrand_bytes": 10_000_000,
            "testu01_bytes": 10_000_000,
            "ea_symbols": 10_000_000,
        }
    return {
        "ond_samples": 10_000,
        "nist_bits": 1_000_000,
        "practrand_bytes": 1_000_000,
        "testu01_bytes": 1_000_000,
        "ea_symbols": 1_000_000,
    }


def _resolve_int(value: int | None, fallback: int) -> int:
    return int(value) if value is not None else int(fallback)


def _load_text_arg(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


def _load_json_arg(value: str | None) -> Dict[str, Any] | None:
    if not value:
        return None
    if value.startswith("@"):
        payload = Path(value[1:]).read_text(encoding="utf-8")
        return json.loads(payload)
    return json.loads(value)


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
        source = _rng_from_args(_namespace_with(args, rng=args.source))
        return ONDMaxRNG(source=source)
    if name == "masked":
        source = _rng_from_args(_namespace_with(args, rng=args.source))
        return MaskedRNG(source=source, mask_low_bits=args.mask_low_bits)
    if name == "bounded":
        source = _rng_from_args(_namespace_with(args, rng=args.source))
        return BoundedRNG(source=source, bound_bits=args.bound_bits)
    raise ValueError(f"unknown rng: {name}")


def _namespace_with(args: argparse.Namespace, **overrides: Any) -> argparse.Namespace:
    data = vars(args).copy()
    data.update(overrides)
    return argparse.Namespace(**data)


def _write_bytes(path: Path, rng: RNG, total_bytes: int, chunk: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    remaining = total_bytes
    with path.open("wb") as handle:
        for buf in rng.random_bytes_stream(chunk=chunk):
            if remaining <= 0:
                break
            take = buf if len(buf) <= remaining else buf[:remaining]
            handle.write(take)
            remaining -= len(take)


def _write_bits(path: Path, rng: RNG, total_bits: int, fmt: str, chunk_bits: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    remaining = total_bits
    fmt = fmt.lower()
    with path.open("wb") as handle:
        while remaining > 0:
            take_bits = min(remaining, chunk_bits)
            n_bytes = (take_bits + 7) // 8
            raw = rng.random_bytes(n_bytes)
            out = bytearray()
            for b in raw:
                for i in range(8):
                    if len(out) >= take_bits:
                        break
                    bit = (b >> (7 - i)) & 1
                    if fmt == "ascii":
                        out.append(48 + bit)
                    else:
                        out.append(bit)
            handle.write(out)
            remaining -= take_bits


def _run_command(command: str, input_path: Path, log_path: Path | None = None) -> Dict[str, Any]:
    tokens = shlex.split(command)
    tokens = [t.replace("{input}", str(input_path)) for t in tokens]
    if "{input}" not in command:
        tokens.append(str(input_path))
    stdout = None
    stderr = None
    log_file = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path.open("w", encoding="utf-8")
        stdout = log_file
        stderr = log_file
    proc = subprocess.run(tokens, check=False, stdout=stdout, stderr=stderr, text=True)
    if log_file is not None:
        log_file.close()
    return {"returncode": proc.returncode, "command": " ".join(tokens), "log": str(log_path) if log_path else None}


def _run_practrand(rng: RNG, args: argparse.Namespace, log_path: Path) -> Dict[str, Any]:
    cmd = args.practrand_cmd
    if shutil.which(cmd) is None:
        return {"status": "skipped", "reason": f"PractRand binary '{cmd}' not found"}
    word = int(args.practrand_stdin_word)
    if word not in (8, 16, 32, 64):
        return {"status": "error", "reason": "--practrand-stdin-word must be one of 8,16,32,64"}

    extra_args: List[str] = list(args.practrand_args or [])
    if args.practrand_args_str:
        extra_args.extend(shlex.split(args.practrand_args_str))
    cmd_list = [cmd, f"stdin{word}"] + extra_args

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=log_file, stderr=log_file)
    assert proc.stdin is not None

    remaining = args.practrand_bytes
    for buf in rng.random_bytes_stream(chunk=args.practrand_chunk):
        if remaining <= 0:
            break
        take = buf if len(buf) <= remaining else buf[:remaining]
        proc.stdin.write(take)
        remaining -= len(take)
    proc.stdin.close()
    returncode = proc.wait()
    log_file.close()
    return {"status": "ok" if returncode == 0 else "error", "returncode": returncode, "log": str(log_path)}


def _generate_symbols(rng: RNG, n_symbols: int, bits_per_symbol: int) -> bytes:
    if bits_per_symbol == 8:
        return rng.random_bytes(n_symbols)
    if bits_per_symbol == 1:
        n_bytes = (n_symbols + 7) // 8
        raw = rng.random_bytes(n_bytes)
        out = bytearray()
        for b in raw:
            for i in range(8):
                if len(out) >= n_symbols:
                    break
                bit = (b >> (7 - i)) & 1
                out.append(bit)
        return bytes(out)
    max_sym = 1 << bits_per_symbol
    out = bytearray()
    while len(out) < n_symbols:
        buf = rng.random_bytes(1024)
        for b in buf:
            out.append(b % max_sym)
            if len(out) >= n_symbols:
                break
    return bytes(out)


def _parse_min_entropy(stdout: str) -> List[float]:
    import re

    values = []
    patterns = [
        r"min-entropy[^0-9]*([0-9]*\\.?[0-9]+)",
        r"H[_ ]?min[^0-9]*([0-9]*\\.?[0-9]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, stdout, flags=re.IGNORECASE):
            try:
                values.append(float(m.group(1)))
            except Exception:
                pass
    return values


def _git_info(base: Path) -> Dict[str, Any] | None:
    try:
        commit = subprocess.check_output(["git", "-C", str(base), "rev-parse", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "-C", str(base), "status", "--porcelain"], text=True).strip()
        dirty = bool(status)
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return None


def _relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def _resolve_percentiles(args: argparse.Namespace) -> Tuple[float, float, float]:
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
    return percentiles, profile


def _run_ond_suite(args: argparse.Namespace, out_dir: Path, defaults: Dict[str, int]) -> Dict[str, Any]:
    rng = _rng_from_args(args)
    samples = _resolve_int(args.ond_samples, defaults["ond_samples"])
    obs = ObservationMap(dimension=args.ond_dimension, word_bits=args.ond_word_bits, stride=args.ond_stride)
    U = obs.from_rng(rng, samples=samples)

    obs_space = {"type": "Z_mod_m", "modulus": int(obs.modulus), "d": int(args.ond_dimension)}
    pi_id = args.pi_id or f"rng:{args.rng}"
    pi_version = args.pi_version or "1"
    pi_spec_raw = _load_text_arg(args.pi_spec)
    if pi_spec_raw:
        try:
            pi_spec = json.loads(pi_spec_raw)
            pi_spec_hash = hash_json(pi_spec)
        except Exception:
            pi_spec_hash = hash_text(pi_spec_raw)
    else:
        pi_spec_hash = hash_json({"pi_id": pi_id, "pi_version": pi_version, "obs_space": obs_space})

    meta = ObservationsMeta(
        pi_id=pi_id,
        pi_version=pi_version,
        pi_spec_hash=pi_spec_hash,
        obs_space=obs_space,
        spec={"name": "ODD-OBS", "version": "0.1"},
    )

    suite_dir = out_dir / "artifacts" / "ond"
    obs_path = suite_dir / "observations.jsonl"
    write_observations_jsonl(str(obs_path), U, meta, stringify_large_ints=not args.no_stringify_large_ints)

    percentiles, profile = _resolve_percentiles(args)

    notes = []
    if args.note:
        notes.extend(args.note)
    if not any("Diagnostic only; no security claim." in n for n in notes):
        notes.append("Diagnostic only; no security claim.")

    try:
        from ond_random import __version__ as pkg_version
    except Exception:
        pkg_version = "unknown"
    method_version = args.method_version or f"ond-random@{pkg_version}/run-suite"

    topology_enabled = None
    if args.topology == "on":
        topology_enabled = True
    elif args.topology == "off":
        topology_enabled = False

    topology_config = {
        "enabled": topology_enabled,
        "mode": args.topology_mode,
        "embedding": args.topology_embedding,
        "maxdim": args.topology_maxdim,
        "persistence_rel": args.topology_persistence_rel,
        "persistence_min": args.topology_persistence_min,
        "sample_size": args.topology_sample_size,
        "bootstrap_samples": args.topology_bootstrap_samples,
        "bootstrap_seed": args.topology_bootstrap_seed if args.topology_bootstrap_seed is not None else args.bootstrap_seed,
    }

    orbit_enabled = None
    if args.orbit_spectrum == "on":
        orbit_enabled = True
    elif args.orbit_spectrum == "off":
        orbit_enabled = False
    include_zero = None
    if args.orbit_include_zero:
        include_zero = True
    elif args.orbit_exclude_zero:
        include_zero = False
    orbit_config = {
        "enabled": orbit_enabled,
        "topk": args.orbit_topk,
        "include_zero": include_zero,
        "bootstrap_samples": args.orbit_bootstrap_samples,
        "bootstrap_seed": args.orbit_bootstrap_seed if args.orbit_bootstrap_seed is not None else args.bootstrap_seed,
    }

    params = _load_json_arg(args.params_json) or {}
    if args.public_context_hash:
        public_context_hash = args.public_context_hash
    elif args.public_context:
        public_context_hash = hash_text(_load_text_arg(args.public_context) or "")
    else:
        public_context_hash = None

    report = build_ond_art_report(
        observations_path=str(obs_path),
        baseline_observations=args.baseline_observations,
        baseline_report=json.loads(Path(args.baseline_report).read_text(encoding="utf-8")) if args.baseline_report else None,
        baseline_id=args.baseline_id,
        baseline_percentiles=(percentiles[0], percentiles[1], percentiles[2]),
        bins=args.bins,
        max_subspace_dim=args.max_subspace_dim,
        branch_bins=args.branch_bins,
        branch_mode=args.branch_mode,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        topology=topology_config,
        orbit_spectrum=orbit_config,
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

    report_path = suite_dir / "ond_art_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "status": "ok",
        "observations": _relpath(obs_path, out_dir),
        "report": _relpath(report_path, out_dir),
        "metrics": report.get("metrics"),
        "baseline": report.get("baseline"),
    }
    if "topology" in report:
        summary["topology"] = report.get("topology")
    if "orbit_spectrum" in report:
        summary["orbit_spectrum"] = report.get("orbit_spectrum")
    return summary


def _run_nist_suite(args: argparse.Namespace, out_dir: Path, defaults: Dict[str, int]) -> Dict[str, Any]:
    rng = _rng_from_args(args)
    suite_dir = out_dir / "artifacts" / "nist"
    bits = _resolve_int(args.nist_bits, defaults["nist_bits"])
    bits_path = suite_dir / "nist_bits.bin"
    _write_bits(bits_path, rng, total_bits=bits, fmt=args.nist_format, chunk_bits=args.nist_chunk_bits)
    result = {
        "status": "prepared",
        "bits": bits,
        "format": args.nist_format,
        "input": _relpath(bits_path, out_dir),
    }
    if args.nist_command:
        log_path = suite_dir / "nist_command.log"
        cmd_result = _run_command(args.nist_command, bits_path, log_path=log_path)
        result.update(cmd_result)
        result["status"] = "ok" if cmd_result["returncode"] == 0 else "error"
    return result


def _run_testu01_suite(args: argparse.Namespace, out_dir: Path, defaults: Dict[str, int]) -> Dict[str, Any]:
    rng = _rng_from_args(args)
    suite_dir = out_dir / "artifacts" / "testu01"
    bytes_total = _resolve_int(args.testu01_bytes, defaults["testu01_bytes"])
    bytes_path = suite_dir / "testu01_bytes.bin"
    _write_bytes(bytes_path, rng, total_bytes=bytes_total, chunk=args.testu01_chunk)
    result = {
        "status": "prepared",
        "bytes": bytes_total,
        "input": _relpath(bytes_path, out_dir),
    }
    if args.testu01_command:
        log_path = suite_dir / "testu01_command.log"
        cmd_result = _run_command(args.testu01_command, bytes_path, log_path=log_path)
        result.update(cmd_result)
        result["status"] = "ok" if cmd_result["returncode"] == 0 else "error"
    return result


def _run_ea90b_suite(args: argparse.Namespace, out_dir: Path, defaults: Dict[str, int]) -> Dict[str, Any]:
    suite_dir = out_dir / "artifacts" / "ea90b"
    bits_per_symbol = args.ea_bits_per_symbol
    symbols = _resolve_int(args.ea_symbols, defaults["ea_symbols"])
    ea_bin = args.ea_path
    if ea_bin is None:
        ea_bin = "ea_non_iid" if args.ea_track == "non-iid" else "ea_iid"
    if shutil.which(ea_bin) is None and not Path(ea_bin).exists():
        return {"status": "skipped", "reason": f"EntropyAssessment binary '{ea_bin}' not found"}

    rng = _rng_from_args(args)
    data = _generate_symbols(rng, symbols, bits_per_symbol)
    input_path = suite_dir / f"ea_symbols_{bits_per_symbol}b.bin"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(data)

    cmd = [ea_bin, "-c" if args.ea_conditioned else "-i", "-t" if args.ea_truncate else "-a", str(input_path), str(bits_per_symbol)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    log_path = suite_dir / "ea90b.log"
    log_path.write_text(stdout + "\n" + stderr, encoding="utf-8")
    return {
        "status": "ok" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "bits_per_symbol": bits_per_symbol,
        "symbols": symbols,
        "input": _relpath(input_path, out_dir),
        "tool": ea_bin,
        "min_entropy_candidates": _parse_min_entropy(stdout),
        "log": _relpath(log_path, out_dir),
    }


def _summarize_status(suites: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for result in suites.values():
        status = result.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    overall = "ok"
    if counts.get("error"):
        overall = "error"
    elif counts.get("skipped") or counts.get("prepared"):
        overall = "partial"
    return {"overall": overall, "counts": counts}


def run_suite(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    suite_list = _parse_suite_list(args.suite)
    defaults = _mode_defaults(args.mode)
    start = datetime.now(timezone.utc)

    suites: Dict[str, Dict[str, Any]] = {}

    if "ond" in suite_list:
        suites["ond"] = _run_ond_suite(args, out_dir, defaults)
    if "nist" in suite_list:
        suites["nist"] = _run_nist_suite(args, out_dir, defaults)
    if "practrand" in suite_list:
        suite_dir = out_dir / "artifacts" / "practrand"
        rng = _rng_from_args(args)
        log_path = suite_dir / "practrand.log"
        suites["practrand"] = {
            "bytes": _resolve_int(args.practrand_bytes, defaults["practrand_bytes"]),
            "stdin_word": args.practrand_stdin_word,
        }
        practrand_args = _namespace_with(args, practrand_bytes=_resolve_int(args.practrand_bytes, defaults["practrand_bytes"]))
        suites["practrand"].update(_run_practrand(rng, practrand_args, log_path))
    if "testu01" in suite_list:
        suites["testu01"] = _run_testu01_suite(args, out_dir, defaults)
    if "ea90b" in suite_list:
        suites["ea90b"] = _run_ea90b_suite(args, out_dir, defaults)

    summary = _summarize_status(suites)
    end = datetime.now(timezone.utc)

    try:
        from ond_random import __version__ as pkg_version
    except Exception:
        pkg_version = "unknown"

    git_info = _git_info(out_dir)

    metadata = {
        "run": {
            "run_id": f"{start.isoformat()}",
            "created_at": start.isoformat(),
            "finished_at": end.isoformat(),
            "duration_seconds": (end - start).total_seconds(),
            "timezone": "UTC",
        },
        "ond_random_version": pkg_version,
        "python": sys.version,
        "platform": platform.platform(),
        "mode": args.mode,
        "suite": suite_list,
        "git": git_info,
        "rng": {
            "name": args.rng,
            "source": args.source,
            "seed": args.seed,
            "seed2": args.seed2,
            "key_hex": args.key_hex,
            "bias": args.bias,
            "drift_sigma": args.drift_sigma,
            "drift_rho": args.drift_rho,
            "memory": args.memory,
            "phase_sigma": args.phase_sigma,
            "mask_low_bits": args.mask_low_bits,
            "bound_bits": args.bound_bits,
        },
        "args": {k: v for k, v in vars(args).items() if k != "func"},
    }

    results = {
        "summary": summary,
        "suites": suites,
    }

    metadata_path = out_dir / "metadata.json"
    results_path = out_dir / "results.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(results, indent=2, sort_keys=True))
    return results
