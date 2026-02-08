from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _split_csv(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _required_artifacts(rngs: list[str], chacha_seeds: list[int]) -> Dict[str, List[str]]:
    required: Dict[str, List[str]] = {}
    for rng in rngs:
        if rng == "chacha20":
            for seed in chacha_seeds:
                required[f"{rng}:seed{seed}"] = [
                    f"practrand/chacha20_seed{seed}_1gb.log",
                    f"nist/chacha20_seed{seed}/result.txt",
                    f"testu01/chacha20_seed{seed}_fips.txt",
                ]
            continue
        required[rng] = [
            f"practrand/{rng}_1gb.log",
            f"nist/{rng}/result.txt",
            f"testu01/{rng}_fips.txt",
        ]
    return required


def _partial_artifacts(rngs: list[str]) -> Dict[str, List[str]]:
    fallback: Dict[str, List[str]] = {}
    if "quantum" in rngs:
        fallback["quantum"] = [
            "practrand/quantum_partial.log",
            "nist/quantum_partial/result.txt",
            "testu01/quantum_partial_fips.txt",
        ]
    return fallback


def _is_present_file(path: Path, rel: str) -> bool:
    if not (path.exists() and path.is_file() and path.stat().st_size > 0):
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = ""

    # Guard against interrupted files that are created but not complete.
    if rel.startswith("practrand/") and rel.endswith("_1gb.log"):
        return "length= 1 gigabyte" in text
    if rel.startswith("testu01/") and rel.endswith("_fips.txt"):
        return "Summary results of FIPS-140-2" in text
    if rel.startswith("nist/") and rel.endswith("/result.txt"):
        return ("A total of" in text) or ("STATISTICAL TEST" in text)
    return True


def _check(root: Path, required: Dict[str, List[str]], fallback: Dict[str, List[str]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    total_files = 0
    present_full_files = 0
    full_targets = 0
    covered_targets = 0
    for name, rels in required.items():
        missing = []
        found_full = []
        for rel in rels:
            total_files += 1
            p = root / rel
            if _is_present_file(p, rel):
                present_full_files += 1
                found_full.append(rel)
            else:
                missing.append(rel)

        row: Dict[str, Any] = {
            "target": name,
            "required": rels,
            "present": found_full,
            "missing": missing,
            "status": "ok" if not missing else "missing",
            "coverage_level": "full" if not missing else "missing",
        }
        if not missing:
            full_targets += 1
            covered_targets += 1
            rows.append(row)
            continue

        partial_rels = fallback.get(name, [])
        partial_present = [rel for rel in partial_rels if _is_present_file(root / rel, rel)]
        if partial_rels and len(partial_present) == len(partial_rels):
            row["status"] = "partial"
            row["coverage_level"] = "partial"
            row["partial_required"] = partial_rels
            row["partial_present"] = partial_present
            covered_targets += 1
        rows.append(row)

    coverage = (present_full_files / total_files) if total_files else 1.0
    full_target_coverage = (full_targets / len(required)) if required else 1.0
    target_coverage = (covered_targets / len(required)) if required else 1.0
    return {
        "root": str(root),
        "total_required_files": total_files,
        "present_files": present_full_files,
        "coverage_ratio": coverage,
        "full_target_coverage_ratio": full_target_coverage,
        "target_coverage_ratio": target_coverage,
        "targets": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check external battery artifact completeness for competitor comparison."
    )
    parser.add_argument("--root", default="data/reports/external/large", help="root with large external artifacts")
    parser.add_argument(
        "--rngs",
        default="ondmax,system,chacha20,lcg,xorshift,quantum",
        help="comma-separated RNG list",
    )
    parser.add_argument("--chacha-seeds", default="1,2,3", help="comma-separated seeds for chacha20")
    parser.add_argument("--out", help="optional JSON output path")
    parser.add_argument("--strict", action="store_true", help="return non-zero if any artifact is missing")
    args = parser.parse_args()

    root = Path(args.root)
    rngs = _split_csv(args.rngs)
    chacha_seeds = [int(s) for s in _split_csv(args.chacha_seeds)]

    required = _required_artifacts(rngs, chacha_seeds)
    fallback = _partial_artifacts(rngs)
    report = _check(root, required, fallback)
    missing_targets = [x for x in report["targets"] if x["status"] == "missing"]
    partial_targets = [x for x in report["targets"] if x["status"] == "partial"]
    report["missing_targets"] = [x["target"] for x in missing_targets]
    report["partial_targets"] = [x["target"] for x in partial_targets]
    if missing_targets:
        report["status"] = "incomplete"
    elif partial_targets:
        report["status"] = "partial"
    else:
        report["status"] = "ok"

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.strict and (missing_targets or partial_targets):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
