from ond_random.quantum.lindblad import QubitHamiltonian, QubitNoise, LindbladQubit, simulate_relaxation


def test_lindblad_relaxation():
    model = LindbladQubit(
        hamiltonian=QubitHamiltonian(omega_z=1.0),
        noise=QubitNoise(gamma1=0.1, gamma_phi=0.05),
    )
    model.step(0.1)
    val = model.expectation_z()
    assert -1.0 <= val <= 1.0


def test_simulate_relaxation():
    values = simulate_relaxation(t_max=1.0, steps=10, gamma1=0.1, gamma_phi=0.05)
    assert len(values) == 10
    assert all(-1.0 <= v <= 1.0 for v in values)


def test_lindblad_rk4_trace():
    model = LindbladQubit(
        hamiltonian=QubitHamiltonian(omega_z=1.0),
        noise=QubitNoise(gamma1=0.1, gamma_phi=0.05),
    )
    model.step_rk4(0.1)
    tr = model.rho.trace().real
    assert abs(tr - 1.0) < 1e-6
