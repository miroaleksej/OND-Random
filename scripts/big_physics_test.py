from __future__ import annotations

import argparse
import numpy as np

from ond_random import MultiQubitHamiltonian, MultiQubitNoise, LindbladSystem, ONDMaxRNG, SystemRNG


def sample_from_diagonal(diag: np.ndarray, shots: int, rng: ONDMaxRNG) -> dict[int, int]:
    cum = np.cumsum(diag)
    counts = {}
    for _ in range(shots):
        r = rng.random_uint(1 << 64) / float(1 << 64)
        idx = int(np.searchsorted(cum, r, side="right"))
        if idx >= cum.size:
            idx = cum.size - 1
        counts[idx] = counts.get(idx, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=6)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--shots", type=int, default=2048)
    args = parser.parse_args()

    n = args.qubits
    steps = args.steps

    system = LindbladSystem(
        n_qubits=n,
        hamiltonian=MultiQubitHamiltonian(
            n_qubits=n,
            omega_z=[1.0] * n,
            couplings_zz={(i, i + 1): 0.15 for i in range(n - 1)},
        ),
        noise=MultiQubitNoise(
            gamma1=[0.05] * n,
            gamma_phi=[0.02] * n,
        ),
    )

    for _ in range(steps):
        system.step(args.dt)

    exp = [system.expectation_z(i) for i in range(n)]
    print("Expectation Z per qubit:")
    print(exp)

    diag = np.real(np.diag(system.rho))
    diag = diag / diag.sum()

    rng = ONDMaxRNG(SystemRNG())
    counts = sample_from_diagonal(diag, args.shots, rng)
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    print("Top measurement outcomes (index, count):")
    print(top)


if __name__ == "__main__":
    main()
