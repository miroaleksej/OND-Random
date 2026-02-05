from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from scripts import numeric_validation


def _max_abs_error(records: list[dict[str, Any]], key_pred: str, key_true: str) -> float:
    if not records:
        return float("nan")
    return max(abs(float(r[key_pred]) - float(r[key_true])) for r in records)


def _load_thresholds(path: str | None) -> Dict[str, float]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    thresholds: Dict[str, float] = {}
    for key, value in data.items():
        if key == "version":
            continue
        thresholds[key] = float(value)
    return thresholds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thresholds", default="docs/accuracy_thresholds.json")
    parser.add_argument("--out", default="data/reports/accuracy_report.json")
    args = parser.parse_args()

    report: Dict[str, Any] = {}
    report.update(numeric_validation.dt_scan())
    report.update(numeric_validation.gamma_scan())
    report.update(numeric_validation.trace_multi_qubit())
    report.update(numeric_validation.grover_validation())

    metrics = {
        "dt_scan_max_error": _max_abs_error(report["dt_scan"], "expect_z", "analytic_z"),
        "dt_scan_rk4_max_error": _max_abs_error(report["dt_scan_rk4"], "expect_z", "analytic_z"),
        "gamma_scan_max_error": _max_abs_error(report["gamma_scan"], "expect_z", "analytic_z"),
        "grover_theory_error": abs(float(report["grover"]["prob"]) - float(report["grover"]["theoretical"])),
        "multi_trace_error": abs(float(report["multi_trace"]["trace"]) - 1.0),
    }

    thresholds = _load_thresholds(args.thresholds)
    checks = {}
    for key, value in metrics.items():
        thr = thresholds.get(key)
        ok = True if thr is None else (value <= thr)
        checks[key] = {"value": value, "threshold": thr, "ok": ok}

    status = "PASS" if all(c["ok"] for c in checks.values()) else "FAIL"

    payload = {
        "status": status,
        "metrics": metrics,
        "thresholds": thresholds,
        "checks": checks,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
