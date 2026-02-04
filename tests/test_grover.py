from ond_random.quantum.grover import grover_state, grover_iterations, grover_search, grover_theta


def test_grover_probability_power_of_two():
    n_items = 128
    target = 37
    iterations = grover_iterations(n_items)
    state = grover_state([target], n_items, iterations=iterations)
    prob = (state[target].real ** 2 + state[target].imag ** 2)
    assert prob > 0.9


def test_grover_probability_non_power_of_two():
    n_items = 100
    target = 42
    iterations = grover_iterations(n_items)
    state = grover_state([target], n_items, iterations=iterations)
    prob = (state[target].real ** 2 + state[target].imag ** 2)
    assert prob > 0.7


def test_grover_multi_target():
    result = grover_search(targets=[5, 9], n_items=64, shots=50)
    assert result.success_prob > 0.8


def test_grover_theta():
    theta = grover_theta(100, n_qubits=7, n_solutions=1)
    assert theta > 0.0


def test_grover_theoretical_amplitude():
    result = grover_search(target=3, n_items=64, shots=20)
    assert -1.0 <= result.theoretical_amplitude <= 1.0
