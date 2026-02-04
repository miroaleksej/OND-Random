from __future__ import annotations

import argparse
import json
import math


def _parse_queries(q: str) -> float:
    s = q.strip().lower()
    if s.startswith("2^"):
        return float(2 ** int(s[2:]))
    return float(s)


def leftover_hash_lemma(k: float, m: float) -> float:
    # Δ ≤ 1/2 * sqrt(2^(m-k))
    return 0.5 * (2 ** ((m - k) / 2.0))


def sponge_bound(q: float, capacity: float) -> float:
    # Adv ≤ q^2 / 2^(c+1)
    if q <= 0:
        return 0.0
    return (q * q) / (2 ** (capacity + 1.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-entropy", type=float, required=True)
    parser.add_argument("--output-bits", type=float, required=True)
    parser.add_argument("--capacity", type=float, default=512.0)
    parser.add_argument("--queries", type=str, default="2^32")
    args = parser.parse_args()

    k = float(args.min_entropy)
    m = float(args.output_bits)
    q = _parse_queries(args.queries)
    c = float(args.capacity)

    eps_lhl = leftover_hash_lemma(k, m)
    eps_sponge = sponge_bound(q, c)

    out = {
        "inputs": {
            "min_entropy": k,
            "output_bits": m,
            "capacity": c,
            "queries": q,
        },
        "leftover_hash_lemma": {
            "epsilon": eps_lhl,
            "log2_epsilon": math.log2(eps_lhl) if eps_lhl > 0 else float("-inf"),
        },
        "sponge_bound": {
            "advantage": eps_sponge,
            "log2_advantage": math.log2(eps_sponge) if eps_sponge > 0 else float("-inf"),
        },
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
