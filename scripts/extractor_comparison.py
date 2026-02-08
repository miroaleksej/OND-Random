from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from ond_random.ond import ObservationMap, compute_profile
from ond_random.rng.base import RNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from ond_random.rng.extractor import ONDMaxRNG, ToeplitzExtractorRNG
from ond_random.rng.structured import MaskedRNG, BoundedRNG


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


def _profile_from_bytes(data: bytes, obs: ObservationMap, modulus: bool) -> Dict[str, Any]:
    U = obs.from_bytes(data)
    profile = compute_profile(U, modulus=obs.modulus if modulus else None)
    return profile.as_dict()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rng", choices=["system", "lcg", "xorshift", "chacha20", "quantum", "ondmax", "masked", "bounded"], default="system")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--seed2", type=int)
    parser.add_argument("--key-hex", dest="key_hex")
    parser.add_argument("--source", choices=["system", "lcg", "xorshift", "chacha20", "quantum"], default="system")
    parser.add_argument("--bias", type=float, default=0.0)
    parser.add_argument("--drift-sigma", type=float, default=1e-3)
    parser.add_argument("--drift-rho", type=float, default=0.999)
    parser.add_argument("--memory", type=float, default=0.0)
    parser.add_argument("--phase-sigma", type=float, default=0.0)
    parser.add_argument("--mask-low-bits", type=int, default=4)
    parser.add_argument("--bound-bits", type=int, default=12)
    parser.add_argument("--output-bytes", type=int, default=1_000_000)
    parser.add_argument("--toeplitz-input-bytes", type=int, default=None)
    parser.add_argument("--toeplitz-output-bytes", type=int, default=1024)
    parser.add_argument("--ond-dimension", type=int, default=4)
    parser.add_argument("--ond-word-bits", type=int, default=32)
    parser.add_argument("--ond-stride", type=int, default=1)
    parser.add_argument("--modulus", action="store_true")
    parser.add_argument("--out", default="data/reports/extractor_comparison.json")
    args = parser.parse_args()

    obs = ObservationMap(dimension=args.ond_dimension, word_bits=args.ond_word_bits, stride=args.ond_stride)
    out_bytes = args.output_bytes
    toeplitz_in = args.toeplitz_input_bytes or out_bytes * 2
    toeplitz_out = min(args.toeplitz_output_bytes, out_bytes)

    results: Dict[str, Any] = {"output_bytes": out_bytes, "methods": {}}

    for method in ("raw", "ondmax", "toeplitz"):
        rng = _rng_from_args(args)
        start = time.perf_counter()
        if method == "raw":
            data = rng.random_bytes(out_bytes)
        elif method == "ondmax":
            extractor = ONDMaxRNG(source=rng)
            data = extractor.random_bytes(out_bytes)
        else:
            extractor = ToeplitzExtractorRNG(source=rng, input_bytes=toeplitz_in, output_bytes=toeplitz_out)
            data = extractor.random_bytes(out_bytes)
        elapsed = time.perf_counter() - start
        profile = _profile_from_bytes(data, obs, args.modulus)
        results["methods"][method] = {
            "elapsed_seconds": elapsed,
            "throughput_bytes_per_sec": out_bytes / elapsed if elapsed > 0 else None,
            "profile": profile,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
