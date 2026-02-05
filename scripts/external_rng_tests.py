from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ond_random.rng.base import RNG
from ond_random.rng.system import SystemRNG
from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel
from ond_random.rng.extractor import ONDMaxRNG
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
                        out.append(48 + bit)  # '0' or '1'
                    else:
                        out.append(bit)
            handle.write(out)
            remaining -= take_bits


def _run_command(command: str, input_path: Path | None = None) -> int:
    tokens = shlex.split(command)
    if input_path is not None:
        tokens = [t.replace("{input}", str(input_path)) for t in tokens]
        if "{input}" not in command:
            tokens.append(str(input_path))
    proc = subprocess.run(tokens, check=False)
    return proc.returncode


def _run_practrand(rng: RNG, args: argparse.Namespace) -> int:
    cmd = args.practrand_cmd
    if shutil.which(cmd) is None:
        raise SystemExit(
            "PractRand binary not found. Install PractRand and ensure RNG_test is in PATH "
            "or pass --practrand-cmd."
        )

    word = int(args.stdin_word)
    if word not in (8, 16, 32, 64):
        raise SystemExit("--stdin-word must be one of: 8, 16, 32, 64")

    extra_args: List[str] = list(args.practrand_args or [])
    if args.practrand_args_str:
        extra_args.extend(shlex.split(args.practrand_args_str))
    cmd_list = [cmd, f"stdin{word}"] + extra_args

    stdout = None
    stderr = None
    if args.log:
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path.open("w", encoding="utf-8")
        stdout = log_file
        stderr = log_file

    proc = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
    assert proc.stdin is not None

    remaining = args.total_bytes
    for buf in rng.random_bytes_stream(chunk=args.chunk):
        if remaining <= 0:
            break
        take = buf if len(buf) <= remaining else buf[:remaining]
        proc.stdin.write(take)
        remaining -= len(take)

    proc.stdin.close()
    return proc.wait()


def _add_rng_args(parser: argparse.ArgumentParser) -> None:
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


def cmd_export(args: argparse.Namespace) -> int:
    rng = _rng_from_args(args)
    out = Path(args.out)
    _write_bytes(out, rng, total_bytes=args.bytes, chunk=args.chunk)
    print(json.dumps({"out": str(out), "bytes": args.bytes, "rng": args.rng}, indent=2, sort_keys=True))
    return 0


def cmd_practrand(args: argparse.Namespace) -> int:
    rng = _rng_from_args(args)
    return _run_practrand(rng, args)


def cmd_nist_sts(args: argparse.Namespace) -> int:
    rng = _rng_from_args(args)
    out = Path(args.out)
    _write_bits(out, rng, total_bits=args.bits, fmt=args.format, chunk_bits=args.chunk_bits)
    print(json.dumps({"out": str(out), "bits": args.bits, "format": args.format}, indent=2, sort_keys=True))
    if args.command:
        return _run_command(args.command, out)
    return 0


def cmd_testu01(args: argparse.Namespace) -> int:
    rng = _rng_from_args(args)
    out = Path(args.out)
    _write_bytes(out, rng, total_bytes=args.bytes, chunk=args.chunk)
    print(json.dumps({"out": str(out), "bytes": args.bytes, "rng": args.rng}, indent=2, sort_keys=True))
    if args.command:
        return _run_command(args.command, out)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="export raw bytes from RNG")
    _add_rng_args(p_export)
    p_export.add_argument("--bytes", type=int, default=1_000_000)
    p_export.add_argument("--out", default="data/external/rng_bytes.bin")
    p_export.add_argument("--chunk", type=int, default=1 << 20)
    p_export.set_defaults(func=cmd_export)

    p_pr = sub.add_parser("practrand", help="stream RNG into PractRand RNG_test")
    _add_rng_args(p_pr)
    p_pr.add_argument("--total-bytes", type=int, default=1_000_000)
    p_pr.add_argument("--stdin-word", type=int, default=64)
    p_pr.add_argument("--practrand-cmd", default="RNG_test")
    p_pr.add_argument("--practrand-args", nargs="*", default=[])
    p_pr.add_argument("--practrand-args-str", default=None, help="optional raw args string passed to RNG_test")
    p_pr.add_argument("--chunk", type=int, default=1 << 20)
    p_pr.add_argument("--log", default=None, help="optional log file path")
    p_pr.set_defaults(func=cmd_practrand)

    p_nist = sub.add_parser("nist-sts", help="prepare bitstream for NIST STS")
    _add_rng_args(p_nist)
    p_nist.add_argument("--bits", type=int, default=1_000_000)
    p_nist.add_argument("--format", choices=["byte", "ascii"], default="byte")
    p_nist.add_argument("--chunk-bits", type=int, default=1 << 20)
    p_nist.add_argument("--out", default="data/external/nist_sts_bits.bin")
    p_nist.add_argument("--command", help="optional command to run (use {input} placeholder)")
    p_nist.set_defaults(func=cmd_nist_sts)

    p_tu = sub.add_parser("testu01", help="prepare raw bytes for TestU01")
    _add_rng_args(p_tu)
    p_tu.add_argument("--bytes", type=int, default=1_000_000)
    p_tu.add_argument("--out", default="data/external/testu01_bytes.bin")
    p_tu.add_argument("--chunk", type=int, default=1 << 20)
    p_tu.add_argument("--command", help="optional command to run (use {input} placeholder)")
    p_tu.set_defaults(func=cmd_testu01)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
