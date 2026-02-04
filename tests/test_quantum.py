import numpy as np

from ond_random.quantum import QuantumState, H, bell_state_correlations, rabi_oscillation, quantum_random_walk, monte_carlo_integral


def test_bell_correlation():
    res = bell_state_correlations(shots=256)
    assert set(res.counts.keys()) == {"00", "01", "10", "11"}
    assert -1.0 <= res.correlation <= 1.0


def test_rabi_output():
    values = rabi_oscillation(theta=0.1, steps=5, shots=128)
    assert len(values) == 5
    assert all(-1.0 <= v <= 1.0 for v in values)


def test_quantum_random_walk():
    dist = quantum_random_walk(steps=4, shots=128)
    assert isinstance(dist, dict)
    assert all(isinstance(k, int) for k in dist.keys())
    assert all(0.0 <= v <= 1.0 for v in dist.values())


def test_monte_carlo_integral():
    estimate = monte_carlo_integral(lambda x: np.ones_like(x), 0.0, 1.0, samples=1000)
    assert 0.9 <= estimate <= 1.1
