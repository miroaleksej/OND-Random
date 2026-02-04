from __future__ import annotations

import argparse
import json
from pathlib import Path

from ond_random.quantum.shor import shor_factor


def run_trials(N: int, a: int, shots: int, trials: int, gamma1: float | None, gamma_phi: float | None) -> dict:
    successes = 0
    for _ in range(trials):
        res = shor_factor(N=N, a=a, shots=shots, gamma1=gamma1, gamma_phi=gamma_phi)
        if res.factors is not None:
            successes += 1
    return {
        "N": N,
        "a": a,
        "shots": shots,
        "trials": trials,
        "gamma1": gamma1,
        "gamma_phi": gamma_phi,
        "success_rate": successes / trials,
        "successes": successes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", type=int, default=2)
    parser.add_argument("--shots", type=int, default=50)
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--gamma1", type=float, default=0.05)
    parser.add_argument("--gamma-phi", dest="gamma_phi", type=float, default=0.02)
    parser.add_argument("--out", default="data/reports/shor_noise_report.json")
    args = parser.parse_args()

    results = []
    for N in (15, 21, 35):
        ideal = run_trials(N, args.a, args.shots, args.trials, None, None)
        noisy = run_trials(N, args.a, args.shots, args.trials, args.gamma1, args.gamma_phi)
        results.append({"N": N, "ideal": ideal, "noisy": noisy})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
