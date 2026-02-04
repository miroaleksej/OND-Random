from __future__ import annotations

import json
from pathlib import Path
import time

import numpy as np

from ond_random.quantum.lindblad import QubitHamiltonian, QubitNoise, LindbladQubit
from ond_random.quantum.lindblad_multi import MultiQubitHamiltonian, MultiQubitNoise, LindbladSystem
from ond_random.quantum.grover import grover_state, grover_iterations, grover_theta


def _analytic_z_from_excited(t: float, gamma1: float) -> float:
    # P1(t) = exp(-gamma1 * t); Z = 1 - 2*P1
    return 1.0 - 2.0 * float(np.exp(-gamma1 * t))


def dt_scan(total_time: float = 4.0) -> dict:
    results = []
    for dt in [0.2, 0.1, 0.05, 0.02]:
        model = LindbladQubit(
            hamiltonian=QubitHamiltonian(omega_z=1.0),
            noise=QubitNoise(gamma1=0.2, gamma_phi=0.02),
        )
        # start in excited state |1>
        model.rho = np.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=complex)
        steps = max(1, int(total_time / dt))
        for _ in range(steps):
            model.step(dt)
        tr = float(np.trace(model.rho).real)
        theo = _analytic_z_from_excited(steps * dt, gamma1=0.2)
        results.append({"dt": dt, "trace": tr, "expect_z": model.expectation_z(), "analytic_z": theo})
    # RK4 comparison
    rk4_results = []
    for dt in [0.2, 0.1, 0.05, 0.02]:
        model = LindbladQubit(
            hamiltonian=QubitHamiltonian(omega_z=1.0),
            noise=QubitNoise(gamma1=0.2, gamma_phi=0.02),
        )
        model.rho = np.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=complex)
        steps = max(1, int(total_time / dt))
        for _ in range(steps):
            model.step_rk4(dt)
        tr = float(np.trace(model.rho).real)
        theo = _analytic_z_from_excited(steps * dt, gamma1=0.2)
        rk4_results.append({"dt": dt, "trace": tr, "expect_z": model.expectation_z(), "analytic_z": theo})
    return {"dt_scan": results, "dt_scan_rk4": rk4_results}


def gamma_scan() -> dict:
    results = []
    for g1 in [0.0, 0.05, 0.1, 0.2]:
        model = LindbladQubit(
            hamiltonian=QubitHamiltonian(omega_z=1.0),
            noise=QubitNoise(gamma1=g1, gamma_phi=0.02),
        )
        # start in excited state |1>
        model.rho = np.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=complex)
        total_time = 5.0
        dt = 0.05
        steps = int(total_time / dt)
        for _ in range(steps):
            model.step_rk4(dt)
        theo = _analytic_z_from_excited(total_time, gamma1=g1)
        results.append({"gamma1": g1, "expect_z": model.expectation_z(), "analytic_z": theo})
    return {"gamma_scan": results}


def trace_multi_qubit(n_qubits: int = 3) -> dict:
    system = LindbladSystem(
        n_qubits=n_qubits,
        hamiltonian=MultiQubitHamiltonian(n_qubits=n_qubits, omega_z=[1.0] * n_qubits),
        noise=MultiQubitNoise(gamma1=[0.05] * n_qubits, gamma_phi=[0.02] * n_qubits),
    )
    # start in |1,0,0,...>
    system.rho = np.zeros_like(system.rho)
    system.rho[1, 1] = 1.0 + 0.0j
    system.step_rk4(0.1)
    tr = float(np.trace(system.rho).real)
    return {"multi_trace": {"n_qubits": n_qubits, "trace": tr}}


def grover_validation(n_items: int = 1000, target: int = 123) -> dict:
    iters = grover_iterations(n_items)
    state = grover_state([target], n_items, iterations=iters)
    prob = float((state[target].real ** 2 + state[target].imag ** 2))
    theta = grover_theta(n_items)
    theo = float(np.sin((2 * iters + 1) * theta) ** 2)
    return {"grover": {"n_items": n_items, "iterations": iters, "prob": prob, "theoretical": theo}}


def perf_smoke() -> dict:
    t0 = time.time()
    _ = grover_state([42], 256, iterations=grover_iterations(256))
    t1 = time.time()
    return {"perf": {"grover_256_state_s": t1 - t0}}


def main() -> None:
    report = {}
    report.update(dt_scan())
    report.update(gamma_scan())
    report.update(trace_multi_qubit())
    report.update(grover_validation())
    report.update(perf_smoke())

    out = Path("data/reports/numeric_validation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    # Optional plots
    try:
        import matplotlib.pyplot as plt  # type: ignore

        plots_dir = Path("data/reports/plots")
        plots_dir.mkdir(parents=True, exist_ok=True)

        # dt scan plot
        dt = [r["dt"] for r in report["dt_scan"]]
        z_euler = [r["expect_z"] for r in report["dt_scan"]]
        z_rk4 = [r["expect_z"] for r in report["dt_scan_rk4"]]
        z_analytic = [r["analytic_z"] for r in report["dt_scan"]]
        plt.figure()
        plt.plot(dt, z_euler, "o-", label="Euler")
        plt.plot(dt, z_rk4, "s-", label="RK4")
        plt.plot(dt, z_analytic, "k--", label="Analytic")
        plt.xlabel("dt")
        plt.ylabel("Z expectation")
        plt.title("Lindblad dt-scan (excited state)")
        plt.legend()
        plt.gca().invert_xaxis()
        plt.tight_layout()
        plt.savefig(plots_dir / "dt_scan.png", dpi=160)
        plt.close()

        # gamma scan plot
        g1 = [r["gamma1"] for r in report["gamma_scan"]]
        z_num = [r["expect_z"] for r in report["gamma_scan"]]
        z_theo = [r["analytic_z"] for r in report["gamma_scan"]]
        plt.figure()
        plt.plot(g1, z_num, "o-", label="RK4")
        plt.plot(g1, z_theo, "k--", label="Analytic")
        plt.xlabel("gamma1")
        plt.ylabel("Z expectation")
        plt.title("Lindblad gamma1-scan (excited state)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "gamma_scan.png", dpi=160)
        plt.close()
    except Exception as exc:
        print(f"plots skipped: {exc}")


if __name__ == "__main__":
    main()
