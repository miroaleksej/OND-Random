from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from ond_random.rng.conditioning import evaluate_toeplitz_conditioning


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _infer_symbols(input_path: str | None, bits_per_symbol: int, explicit_symbols: int | None) -> Optional[int]:
    if explicit_symbols is not None:
        return explicit_symbols
    if input_path is None:
        return None
    p = Path(input_path)
    if not p.exists():
        return None
    return p.stat().st_size


def _min_entropy_per_symbol(report: Dict[str, Any]) -> Optional[float]:
    values = report.get("min_entropy_candidates")
    if not isinstance(values, list) or not values:
        return None
    try:
        return float(min(values))
    except Exception:
        return None


def _extract_from_ea_report(path: str, symbols: int | None) -> Optional[float]:
    report = _load_json(path)
    bits_per_symbol = int(report.get("bits_per_symbol", 8))
    input_path = report.get("input")
    count = _infer_symbols(input_path, bits_per_symbol, symbols)
    per_symbol = _min_entropy_per_symbol(report)
    if per_symbol is None or count is None:
        return None
    return float(per_symbol * count)


def _extract_from_run_suite(path: str) -> Optional[float]:
    data = _load_json(path)
    suites = data.get("suites", {})
    ea = suites.get("ea90b", {})
    if not isinstance(ea, dict):
        return None
    per_symbol = ea.get("min_entropy_candidates")
    if not isinstance(per_symbol, list) or not per_symbol:
        return None
    try:
        per_symbol_value = float(min(per_symbol))
    except Exception:
        return None
    symbols = ea.get("symbols")
    if symbols is None:
        return None
    return float(per_symbol_value * float(symbols))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["ondmax", "toeplitz"], required=True)
    parser.add_argument("--output-bits", type=int, required=True)
    parser.add_argument("--epsilon", type=float, default=2 ** -32)
    parser.add_argument("--min-entropy-bits", type=float, default=None)
    parser.add_argument("--min-entropy-per-symbol", type=float, default=None)
    parser.add_argument("--symbols", type=int, default=None)
    parser.add_argument("--ea-report", help="NIST EntropyAssessment report JSON")
    parser.add_argument("--run-suite-results", help="results.json from run-suite")
    parser.add_argument("--out", default="data/reports/conditioning_report.json")
    args = parser.parse_args()

    observed = None
    if args.min_entropy_bits is not None:
        observed = float(args.min_entropy_bits)
    elif args.min_entropy_per_symbol is not None and args.symbols is not None:
        observed = float(args.min_entropy_per_symbol * args.symbols)
    elif args.ea_report:
        observed = _extract_from_ea_report(args.ea_report, args.symbols)
    elif args.run_suite_results:
        observed = _extract_from_run_suite(args.run_suite_results)

    report: Dict[str, Any] = {
        "method": args.method,
        "output_bits": args.output_bits,
        "epsilon": args.epsilon,
        "observed_min_entropy_bits": observed,
    }

    if args.method == "toeplitz":
        report.update(evaluate_toeplitz_conditioning(args.output_bits, args.epsilon, observed))
    else:
        report["status"] = "unknown"
        report["note"] = "ONDMaxRNG is a practical SHAKE256-based extractor without information-theoretic guarantees."

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
