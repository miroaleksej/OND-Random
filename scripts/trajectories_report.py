from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ond_random.quantum.lindblad_multi import MultiQubitHamiltonian, MultiQubitNoise, LindbladSystem
from ond_random.quantum.trajectories import simulate_trajectories


def _basis_state(index: int, size: int) -> np.ndarray:
    psi = np.zeros(size, dtype=complex)
    psi[index] = 1.0 + 0.0j
    return psi


def _run_case(n_qubits: int, steps: int, dt: float, trajectories: int, gamma1: float, gamma_phi: float) -> dict:
    H = MultiQubitHamiltonian(n_qubits=n_qubits, omega_z=[1.0] * n_qubits)
    noise = MultiQubitNoise(gamma1=[gamma1] * n_qubits, gamma_phi=[gamma_phi] * n_qubits)

    # start in |1,0,0,...>
    size = 1 << n_qubits
    index = 1

    # Lindblad (density matrix)
    system = LindbladSystem(n_qubits=n_qubits, hamiltonian=H, noise=noise)
    system.rho = np.zeros((size, size), dtype=complex)
    system.rho[index, index] = 1.0 + 0.0j
    for _ in range(steps):
        system.step_rk4(dt)
    lindblad = [system.expectation_z(i) for i in range(n_qubits)]

    # Trajectories (wavefunction)
    init = _basis_state(index, size)
    traj = simulate_trajectories(
        n_qubits=n_qubits,
        steps=steps,
        dt=dt,
        hamiltonian=H,
        noise=noise,
        trajectories=trajectories,
        initial_state=init,
    )
    traj_exp = traj.expectations_z
    traj_std = traj.expectations_z_std or [0.0] * n_qubits
    traj_sem = traj.expectations_z_sem or [0.0] * n_qubits

    ci_1sigma = [[traj_exp[i] - traj_std[i], traj_exp[i] + traj_std[i]] for i in range(n_qubits)]
    ci_2sigma = [[traj_exp[i] - 2 * traj_std[i], traj_exp[i] + 2 * traj_std[i]] for i in range(n_qubits)]

    diffs = [traj_exp[i] - lindblad[i] for i in range(n_qubits)]
    abs_err = [abs(d) for d in diffs]

    return {
        "n_qubits": n_qubits,
        "steps": steps,
        "dt": dt,
        "trajectories": trajectories,
        "gamma1": gamma1,
        "gamma_phi": gamma_phi,
        "lindblad": lindblad,
        "trajectories_expect": traj_exp,
        "trajectories_std": traj_std,
        "trajectories_sem": traj_sem,
        "ci_1sigma": ci_1sigma,
        "ci_2sigma": ci_2sigma,
        "diff": diffs,
        "abs_err": abs_err,
        "abs_err_mean": float(np.mean(abs_err)),
        "abs_err_max": float(np.max(abs_err)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--trajectories", type=int, default=1000)
    parser.add_argument("--gamma1", type=float, default=0.2)
    parser.add_argument("--gamma-phi", dest="gamma_phi", type=float, default=0.02)
    parser.add_argument("--out", default="data/reports/trajectories_vs_lindblad.json")
    args = parser.parse_args()

    cases = []
    for n_qubits in (1, 2):
        cases.append(
            _run_case(
                n_qubits=n_qubits,
                steps=args.steps,
                dt=args.dt,
                trajectories=args.trajectories,
                gamma1=args.gamma1,
                gamma_phi=args.gamma_phi,
            )
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cases, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(cases, indent=2, sort_keys=True))

    # Optional plots
    try:
        import matplotlib.pyplot as plt  # type: ignore

        plots_dir = Path("data/reports/plots")
        plots_dir.mkdir(parents=True, exist_ok=True)

        for entry in cases:
            n = entry["n_qubits"]
            lindblad = entry["lindblad"]
            traj = entry["trajectories_expect"]
            traj_std = entry["trajectories_std"]
            x = np.arange(n)
            width = 0.35
            plt.figure()
            plt.bar(x - width / 2, lindblad, width, label="Lindblad")
            plt.bar(x + width / 2, traj, width, yerr=traj_std, capsize=4, label="Trajectories (1σ)")
            plt.xlabel("Qubit")
            plt.ylabel("<Z>")
            plt.title(f"Trajectories vs Lindblad (n={n})")
            plt.legend()
            plt.tight_layout()
            plt.savefig(plots_dir / f"trajectories_vs_lindblad_n{n}.png", dpi=160)
            plt.close()
    except Exception as exc:
        print(f"plots skipped: {exc}")


if __name__ == "__main__":
    main()
