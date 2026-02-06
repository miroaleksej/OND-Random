from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from ond_random.ond.observation import ObservationMap
from ond_random.ond.observations_jsonl import ObservationsMeta, write_observations_jsonl
from ond_random.ond.odd_report import build_ond_art_report
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.lcg import LCGRNG


def _hash_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass
class BitTestResult:
    n_bits: int
    ones: int
    p_monobit: float
    runs: int
    p_runs: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "n_bits": int(self.n_bits),
            "ones": int(self.ones),
            "p_monobit": float(self.p_monobit),
            "runs": int(self.runs),
            "p_runs": float(self.p_runs),
        }


def _make_rng(seed: int) -> RNG:
    base = LCGRNG(seed=seed)
    ond = ONDMaxRNG(source=base, personalization=b"OND-CASE-LOWBITS")
    return ond


def _bytes_to_bits(data: bytes) -> List[int]:
    bits: List[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _monobit_p(bits: List[int]) -> float:
    n = len(bits)
    if n == 0:
        return 0.0
    s = sum(1 if b == 1 else -1 for b in bits)
    return float(math.erfc(abs(s) / math.sqrt(2.0 * n)))


def _runs_p(bits: List[int]) -> tuple[float, int]:
    n = len(bits)
    if n < 2:
        return 0.0, 0
    ones = sum(bits)
    pi = ones / n
    if abs(pi - 0.5) >= 2.0 / math.sqrt(n):
        return 0.0, 1
    runs = 1 + sum(1 for i in range(1, n) if bits[i] != bits[i - 1])
    num = abs(runs - 2.0 * n * pi * (1.0 - pi))
    den = 2.0 * math.sqrt(2.0 * n) * pi * (1.0 - pi)
    return float(math.erfc(num / den)), runs


def _bit_tests(U: np.ndarray, n_bits: int) -> BitTestResult:
    data = U.astype(">u4").tobytes()
    bits = _bytes_to_bits(data)[:n_bits]
    ones = int(sum(bits))
    p_mono = _monobit_p(bits)
    p_runs, runs = _runs_p(bits)
    return BitTestResult(n_bits=n_bits, ones=ones, p_monobit=p_mono, runs=runs, p_runs=p_runs)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Low-bits bias demo: bit-tests look ok, OND/ks1-ks2 sees structure.")
    parser.add_argument("--out-dir", default="data/reports/cases/low_bits_bias")
    parser.add_argument("--samples", type=int, default=5000)
    parser.add_argument("--word-bits", type=int, default=32)
    parser.add_argument("--dimension", type=int, default=2)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--offset-low-bits", type=int, default=2)
    parser.add_argument("--bit-tests-bits", type=int, default=200000)
    parser.add_argument("--profile", choices=["core", "recommended", "dev"], default="recommended")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    obs = ObservationMap(dimension=args.dimension, word_bits=args.word_bits, stride=1)
    modulus = obs.modulus

    obs_space = {"type": "Z_mod_m", "modulus": int(modulus), "d": int(args.dimension)}
    pi_spec = {
        "pi_id": "case-low-bits-v1",
        "pi_version": "1.0.0",
        "obs_space": obs_space,
        "description": "ObservationMap(d=2, word_bits=32) over Z_mod_m",
    }
    pi_hash = _hash_json(pi_spec)

    baseline_rng = _make_rng(args.seed)
    U_base = obs.from_rng(baseline_rng, args.samples)

    offset = 1 << int(args.offset_low_bits)
    U_struct = np.array(U_base, copy=True)
    U_struct[:, 1] = (U_struct[:, 0] + offset) % modulus

    meta_base = ObservationsMeta(
        pi_id=pi_spec["pi_id"],
        pi_version=pi_spec["pi_version"],
        pi_spec_hash=pi_hash,
        obs_space=obs_space,
        extras={"variant": "baseline"},
    )
    meta_struct = ObservationsMeta(
        pi_id=pi_spec["pi_id"],
        pi_version=pi_spec["pi_version"],
        pi_spec_hash=pi_hash,
        obs_space=obs_space,
        extras={"variant": f"low_bits_offset_{args.offset_low_bits}"},
    )

    base_obs_path = out_dir / "observations_baseline.jsonl"
    struct_obs_path = out_dir / "observations_low_bits.jsonl"
    write_observations_jsonl(str(base_obs_path), U_base, meta_base)
    write_observations_jsonl(str(struct_obs_path), U_struct, meta_struct)

    orbit_cfg = {"enabled": True, "topk": 8, "include_zero": True, "bootstrap_samples": 50}
    topo_cfg = {"enabled": False}

    baseline_report = build_ond_art_report(
        observations_path=str(base_obs_path),
        baseline_observations=str(base_obs_path),
        bins=16,
        max_subspace_dim=6,
        branch_mode="delta",
        bootstrap_samples=100,
        bootstrap_seed=1,
        topology=topo_cfg,
        orbit_spectrum=orbit_cfg,
        spec_profile=args.profile,
        method_version="ond-random@case/low-bits",
        notes=["Diagnostic only; no security claim.", "Case study: low-bits lag structure."],
    )
    baseline_path = out_dir / "baseline_report.json"
    _write_json(baseline_path, baseline_report)

    structured_report = build_ond_art_report(
        observations_path=str(struct_obs_path),
        baseline_report=baseline_report,
        bins=16,
        max_subspace_dim=6,
        branch_mode="delta",
        bootstrap_samples=100,
        bootstrap_seed=1,
        topology=topo_cfg,
        orbit_spectrum=orbit_cfg,
        spec_profile=args.profile,
        method_version="ond-random@case/low-bits",
        notes=["Diagnostic only; no security claim.", "Case study: low-bits lag structure."],
    )
    report_path = out_dir / "ond_art_report.json"
    _write_json(report_path, structured_report)

    # Bit tests (simple monobit + runs on raw bitstream)
    base_bits = _bit_tests(U_base, args.bit_tests_bits)
    struct_bits = _bit_tests(U_struct, args.bit_tests_bits)
    tests_path = out_dir / "bit_tests.json"
    _write_json(
        tests_path,
        {
            "n_bits": int(args.bit_tests_bits),
            "baseline": base_bits.as_dict(),
            "low_bits_offset": struct_bits.as_dict(),
            "threshold": {"p_value": 0.01},
            "note": "These are simple SP800-22-style monobit/runs checks, not full test batteries.",
        },
    )

    summary_path = out_dir / "case_summary.json"
    _write_json(
        summary_path,
        {
            "baseline_observations": str(base_obs_path),
            "structured_observations": str(struct_obs_path),
            "baseline_report": str(baseline_path),
            "structured_report": str(report_path),
            "bit_tests": str(tests_path),
            "obs_space": obs_space,
            "offset_low_bits": int(args.offset_low_bits),
            "samples": int(args.samples),
            "bit_tests_bits": int(args.bit_tests_bits),
        },
    )

    print(json.dumps({"out_dir": str(out_dir)}, indent=2))


if __name__ == "__main__":
    main()
