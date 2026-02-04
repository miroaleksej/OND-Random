from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def _run(cmd: list[str], env: dict) -> dict:
    t0 = time.time()
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    t1 = time.time()
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "seconds": t1 - t0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--dimension", type=int, default=4)
    parser.add_argument("--word-bits", type=int, default=32)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--modulus", action="store_true")
    parser.add_argument("--branch-mode", choices=["raw", "delta"], default="delta")
    parser.add_argument("--branch-bins", type=int)
    parser.add_argument("--benchmark-out", default="data/benchmarks")
    parser.add_argument("--benchmark-report", default="data/reports/benchmark_profiles.json")
    parser.add_argument("--shor-shots", type=int, default=50)
    parser.add_argument("--shor-trials", type=int, default=50)
    parser.add_argument("--gamma1", type=float, default=0.05)
    parser.add_argument("--gamma-phi", dest="gamma_phi", type=float, default=0.02)
    parser.add_argument("--backend-qubits", type=int, default=20)
    parser.add_argument("--backend-iters", type=int, default=5)
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    steps = []

    bench_cmd = [
        sys.executable,
        "-m",
        "ond_random.cli",
        "benchmark",
        "--out-dir",
        args.benchmark_out,
        "--out-report",
        args.benchmark_report,
        "--samples",
        str(args.samples),
        "--dimension",
        str(args.dimension),
        "--word-bits",
        str(args.word_bits),
        "--stride",
        str(args.stride),
        "--branch-mode",
        args.branch_mode,
        "--auto-calibrate",
        "--calibration-group",
        "id",
    ]
    if args.modulus:
        bench_cmd.append("--modulus")
    if args.branch_bins is not None:
        bench_cmd.extend(["--branch-bins", str(args.branch_bins)])
    steps.append(("benchmark", bench_cmd))

    steps.append(("quality_report", [sys.executable, "scripts/quality_report.py"]))
    steps.append(
        (
            "auto_calibrate",
            [
                sys.executable,
                "scripts/auto_calibrate.py",
                "--ond-class",
                "I",
                "--out",
                "data/reports/auto_calibration_classI.json",
            ],
        )
    )
    steps.append(("numeric_validation", [sys.executable, "scripts/numeric_validation.py"]))
    steps.append(
        (
            "shor_noise_report",
            [
                sys.executable,
                "scripts/shor_noise_report.py",
                "--shots",
                str(args.shor_shots),
                "--trials",
                str(args.shor_trials),
                "--gamma1",
                str(args.gamma1),
                "--gamma-phi",
                str(args.gamma_phi),
            ],
        )
    )
    steps.append(
        (
            "backend_benchmark",
            [
                sys.executable,
                "scripts/benchmark_kernels.py",
                "--qubits",
                str(args.backend_qubits),
                "--iters",
                str(args.backend_iters),
                "--out",
                "data/reports/backend_benchmark.json",
            ],
        )
    )
    steps.append(
        (
            "trajectories_report",
            [
                sys.executable,
                "scripts/trajectories_report.py",
            ],
        )
    )
    steps.append(("system_report", [sys.executable, "scripts/system_report.py"]))

    results = []
    for name, cmd in steps:
        res = _run(cmd, env)
        res["name"] = name
        results.append(res)
        if res["returncode"] != 0:
            break

    summary = {
        "status": "PASS" if all(r["returncode"] == 0 for r in results) else "FAIL",
        "steps": [
            {
                "name": r["name"],
                "returncode": r["returncode"],
                "seconds": r["seconds"],
            }
            for r in results
        ],
    }

    out = Path("data/reports/pipeline_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
