from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from ond_random.rng.system import SystemRNG
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.quantum import QuantumEmulatorRNG, QuantumNoiseModel


def _get_rng(name: str):
    if name == "system":
        return SystemRNG()
    if name == "ondmax":
        return ONDMaxRNG(SystemRNG())
    if name == "quantum":
        return QuantumEmulatorRNG(seed=1, model=QuantumNoiseModel())
    raise ValueError(f"unsupported rng: {name}")


def _generate_symbols(rng_name: str, n_symbols: int, bits_per_symbol: int) -> bytes:
    rng = _get_rng(rng_name)
    if bits_per_symbol == 8:
        return rng.random_bytes(n_symbols)
    if bits_per_symbol == 1:
        # Expand bytes into 0/1 bytes
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
    # Generic: map raw bytes to symbols in [0, 2^b)
    max_sym = 1 << bits_per_symbol
    out = bytearray()
    while len(out) < n_symbols:
        buf = rng.random_bytes(1024)
        for b in buf:
            out.append(b % max_sym)
            if len(out) >= n_symbols:
                break
    return bytes(out)


def _parse_min_entropy(stdout: str) -> list[float]:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="path to raw symbol file")
    parser.add_argument("--rng", choices=["system", "ondmax", "quantum"], help="generate input from RNG")
    parser.add_argument("--symbols", type=int, default=1_000_000, help="number of symbols to generate")
    parser.add_argument("--bits-per-symbol", type=int, default=8)
    parser.add_argument("--track", choices=["iid", "non-iid"], default="non-iid")
    parser.add_argument("--ea-path", help="path to NIST EA binary (ea_non_iid / ea_iid)")
    parser.add_argument("--conditioned", action="store_true", help="use conditioned source mode")
    parser.add_argument("--truncate", action="store_true", help="truncate data to the first 1,000,000 bits")
    parser.add_argument("--analyze-all", action="store_true", help="analyze full data file (default)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--out", default="data/reports/nist_entropy_report.json")
    args = parser.parse_args()

    if not args.input and not args.rng:
        raise SystemExit("provide --input or --rng")

    # Prepare input file
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"input not found: {input_path}")
    else:
        tmp_dir = Path("data/reports")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        input_path = tmp_dir / f"nist_entropy_symbols_{args.bits_per_symbol}b.bin"
        data = _generate_symbols(args.rng, args.symbols, args.bits_per_symbol)
        input_path.write_bytes(data)

    # Locate EA binary
    ea_bin = args.ea_path
    if ea_bin is None:
        ea_bin = "ea_non_iid" if args.track == "non-iid" else "ea_iid"

    cmd = [ea_bin]
    if args.conditioned:
        cmd.append("-c")
    else:
        cmd.append("-i")
    if args.truncate:
        cmd.append("-t")
    else:
        # Tool expects either -a or -t; default to -a
        cmd.append("-a")
    if args.verbose:
        cmd.append("-v")
    cmd.append(str(input_path))
    cmd.append(str(args.bits_per_symbol))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise SystemExit(
            "NIST EntropyAssessment tool not found. Install from usnistgov/SP800-90B_EntropyAssessment "
            "and ensure ea_iid/ea_non_iid is in PATH or pass --ea-path."
        )

    min_entropy_values = _parse_min_entropy(proc.stdout)

    report = {
        "tool": ea_bin,
        "track": args.track,
        "bits_per_symbol": args.bits_per_symbol,
        "input": str(input_path),
        "returncode": proc.returncode,
        "min_entropy_candidates": min_entropy_values,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
