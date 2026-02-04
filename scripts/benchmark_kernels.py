from __future__ import annotations

import argparse
import json

from ond_random.quantum.backend import benchmark_backend, auto_select_backend


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=20)
    parser.add_argument("--iters", type=int, default=5)
    parser.add_argument("--out", default="data/reports/backend_benchmark.json")
    args = parser.parse_args()

    results = benchmark_backend(n_qubits=args.qubits, iters=args.iters)
    best = auto_select_backend(n_qubits=args.qubits, iters=args.iters)

    out = {
        "qubits": args.qubits,
        "iters": args.iters,
        "bench": results,
        "best": best.name,
    }
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
