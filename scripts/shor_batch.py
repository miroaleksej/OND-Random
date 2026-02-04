from __future__ import annotations

import argparse
import json
from pathlib import Path

from ond_random.quantum.shor import shor_factor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", type=int, default=2)
    parser.add_argument("--shots", type=int, default=200)
    parser.add_argument("--gamma1", type=float)
    parser.add_argument("--gamma-phi", dest="gamma_phi", type=float)
    parser.add_argument("--out", default="data/reports/shor_batch.json")
    args = parser.parse_args()

    results = []
    for N in (15, 21, 35):
        res = shor_factor(N=N, a=args.a, shots=args.shots, gamma1=args.gamma1, gamma_phi=args.gamma_phi)
        results.append(res.as_dict())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
