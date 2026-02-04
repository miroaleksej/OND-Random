from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ond_random.quantum.backend import benchmark_backend, auto_select_backend


def _load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _max_abs_error(records, key_pred: str, key_true: str) -> float:
    if not records:
        return float("nan")
    return max(abs(r[key_pred] - r[key_true]) for r in records)


def main() -> None:
    report: Dict[str, Any] = {}

    numeric = _load_json("data/reports/numeric_validation.json")
    report["numeric"] = numeric

    if numeric:
        dt_scan = numeric.get("dt_scan", [])
        dt_scan_rk4 = numeric.get("dt_scan_rk4", [])
        gamma_scan = numeric.get("gamma_scan", [])

        report["numeric_summary"] = {
            "dt_scan_max_error": _max_abs_error(dt_scan, "expect_z", "analytic_z"),
            "dt_scan_rk4_max_error": _max_abs_error(dt_scan_rk4, "expect_z", "analytic_z"),
            "gamma_scan_max_error": _max_abs_error(gamma_scan, "expect_z", "analytic_z"),
        }

    quality = _load_json("data/reports/quality_report.json")
    report["quality"] = quality

    auto_cal = _load_json("data/reports/auto_calibration.json")
    report["auto_calibration"] = auto_cal

    bench = _load_json("data/reports/benchmark_profiles.json")
    report["bench_profiles"] = bench

    shor_noise = _load_json("data/reports/shor_noise_report.json")
    report["shor_noise"] = shor_noise

    traj_report = _load_json("data/reports/trajectories_vs_lindblad.json")
    report["trajectories_vs_lindblad"] = traj_report

    nist_entropy = _load_json("data/reports/nist_entropy_report.json")
    report["nist_entropy"] = nist_entropy

    # Backend benchmarks
    bench_times = benchmark_backend(n_qubits=20, iters=5)
    best = auto_select_backend(n_qubits=20, iters=5)
    report["backend_benchmark"] = {"times": bench_times, "best": best.name}

    # Derived comparisons
    if bench:
        by_id = {p["id"]: p for p in bench}
        if "I-ondmax" in by_id and "Q-drift" in by_id:
            report["ond_diff"] = {
                "H_sub_delta": by_id["I-ondmax"]["H_sub"] - by_id["Q-drift"]["H_sub"],
                "H_branch_delta": by_id["I-ondmax"]["H_branch"] - by_id["Q-drift"]["H_branch"],
            }

    # Write JSON
    out_json = Path("data/reports/system_report.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    # Write markdown
    lines = []
    lines.append("# System Report")
    lines.append("")
    lines.append("## Executive Summary")
    if report.get("numeric_summary"):
        ns = report["numeric_summary"]
        lines.append(f"- Lindblad Euler max error: {ns['dt_scan_max_error']:.3e}")
        lines.append(f"- Lindblad RK4 max error: {ns['dt_scan_rk4_max_error']:.3e}")
        lines.append(f"- Lindblad gamma-scan max error: {ns['gamma_scan_max_error']:.3e}")
    if report.get("quality"):
        lines.append(f"- Quality report status: {report['quality'].get('status', 'N/A')}")
    if report.get("auto_calibration"):
        targets = report["auto_calibration"].get("targets", {})
        updated_key = report["auto_calibration"].get("updated_key", "N/A")
        if targets:
            # Prefer updated key if present
            sample_key = None
            if isinstance(updated_key, str) and updated_key in targets:
                sample_key = updated_key
            elif isinstance(updated_key, list) and updated_key:
                for k in updated_key:
                    if k in targets:
                        sample_key = k
                        break
            if sample_key is None:
                sample_key = list(targets.keys())[0]
            mean = targets[sample_key].get("mean", {})
            lines.append(f"- Online calibration key: {sample_key}")
            lines.append(f"- Online calibration H_rank mean: {mean.get('H_rank', 'N/A')}")
        else:
            lines.append("- Online calibration: no targets")
    if report.get("backend_benchmark"):
        lines.append(f"- Best backend (qubits=20): {report['backend_benchmark']['best']}")
    lines.append("")

    lines.append("## OND Differentials")
    if report.get("ond_diff"):
        diff = report["ond_diff"]
        lines.append(f"- H_sub(IID) - H_sub(Q-drift): {diff['H_sub_delta']:.4f}")
        lines.append(f"- H_branch(IID) - H_branch(Q-drift): {diff['H_branch_delta']:.4f}")
    else:
        lines.append("- Not available (run benchmark first)")
    lines.append("")

    lines.append("## Shor Noise Success")
    if report.get("shor_noise"):
        for entry in report["shor_noise"]:
            N = entry["N"]
            ideal = entry["ideal"]["success_rate"]
            noisy = entry["noisy"]["success_rate"]
            lines.append(f"- N={N}: ideal={ideal:.2f}, noisy={noisy:.2f}")
    else:
        lines.append("- Not available (run shor_noise_report)")

    lines.append("")
    lines.append("## Trajectories vs Lindblad")
    if report.get("trajectories_vs_lindblad"):
        for entry in report["trajectories_vs_lindblad"]:
            lines.append(
                f"- n_qubits={entry['n_qubits']}: mean_abs_err={entry['abs_err_mean']:.3e}, max_abs_err={entry['abs_err_max']:.3e}"
            )
    else:
        lines.append("- Not available (run trajectories_report)")

    lines.append("")
    lines.append("## NIST SP 800-90B Min-Entropy (EntropyAssessment)")
    if report.get("nist_entropy"):
        ne = report["nist_entropy"]
        candidates = ne.get("min_entropy_candidates", [])
        if candidates:
            min_val = min(candidates)
            max_val = max(candidates)
            lines.append(f"- Candidates: {candidates}")
            lines.append(f"- Min: {min_val:.6f}, Max: {max_val:.6f}")
        else:
            lines.append("- No candidates parsed (check nist_entropy_report.json stdout)")
        lines.append(f"- Tool: {ne.get('tool', 'N/A')}")
        lines.append(f"- Track: {ne.get('track', 'N/A')}, Bits/Symbol: {ne.get('bits_per_symbol', 'N/A')}")
    else:
        lines.append("- Not available (run scripts/nist_entropy_estimator.py)")

    out_md = Path("data/reports/system_report.md")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
