import numpy as np

from ond_random.quantum.trajectories import simulate_trajectories
from ond_random.quantum.lindblad_multi import MultiQubitHamiltonian, MultiQubitNoise


def test_trajectories_ground_state_stability():
    res = simulate_trajectories(
        n_qubits=1,
        steps=20,
        dt=0.05,
        hamiltonian=MultiQubitHamiltonian(n_qubits=1, omega_z=1.0),
        noise=MultiQubitNoise(gamma1=0.0, gamma_phi=0.0),
        trajectories=20,
    )
    assert len(res.expectations_z) == 1
    assert np.isclose(res.expectations_z[0], 1.0, atol=1e-3)


def test_trajectories_decay_with_noise():
    init = np.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=complex)
    res = simulate_trajectories(
        n_qubits=1,
        steps=40,
        dt=0.05,
        hamiltonian=MultiQubitHamiltonian(n_qubits=1, omega_z=1.0),
        noise=MultiQubitNoise(gamma1=1.0, gamma_phi=0.0),
        trajectories=50,
        initial_state=init,
    )
    assert res.expectations_z[0] > -0.9
