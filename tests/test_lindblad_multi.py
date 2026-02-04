import numpy as np

from ond_random.quantum.lindblad_multi import MultiQubitHamiltonian, MultiQubitNoise, LindbladSystem


def test_lindblad_multi_trace():
    system = LindbladSystem(
        n_qubits=2,
        hamiltonian=MultiQubitHamiltonian(n_qubits=2, omega_z=[1.0, 1.0]),
        noise=MultiQubitNoise(gamma1=[0.1, 0.1], gamma_phi=[0.05, 0.05]),
    )
    system.step(0.1)
    tr = np.trace(system.rho).real
    assert abs(tr - 1.0) < 1e-6


def test_lindblad_multi_expectation():
    system = LindbladSystem(
        n_qubits=3,
        hamiltonian=MultiQubitHamiltonian(n_qubits=3, omega_z=1.0),
        noise=MultiQubitNoise(gamma1=0.0, gamma_phi=0.0),
    )
    system.step(0.05)
    for i in range(3):
        val = system.expectation_z(i)
        assert -1.0 <= val <= 1.0
