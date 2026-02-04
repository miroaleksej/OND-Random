import numpy as np

from ond_random.quantum.statevector import QuantumState, H, X, Z
from ond_random.quantum.backend import apply_single_qubit, apply_cnot


def _ref_apply_single(state, gate, qubit, n_qubits):
    size = 1 << n_qubits
    mask = 1 << qubit
    out = state.copy()
    for i in range(size):
        if (i & mask) == 0:
            j = i | mask
            a0 = state[i]
            a1 = state[j]
            out[i] = gate[0, 0] * a0 + gate[0, 1] * a1
            out[j] = gate[1, 0] * a0 + gate[1, 1] * a1
    return out


def test_apply_single_qubit_vectorized():
    n = 3
    size = 1 << n
    rng = np.random.default_rng(0)
    state = rng.normal(size=size) + 1j * rng.normal(size=size)
    state = state / np.linalg.norm(state)
    for gate in (H, X, Z):
        out_vec = apply_single_qubit(state.copy(), gate, 1, n, xp=np)
        out_ref = _ref_apply_single(state, gate, 1, n)
        assert np.allclose(out_vec, out_ref)


def test_apply_cnot_vectorized():
    n = 3
    size = 1 << n
    rng = np.random.default_rng(1)
    state = rng.normal(size=size) + 1j * rng.normal(size=size)
    state = state / np.linalg.norm(state)
    out_vec = apply_cnot(state.copy(), control=0, target=2, n_qubits=n, xp=np)
    # reference via explicit swap
    out_ref = state.copy()
    c_mask = 1 << 0
    t_mask = 1 << 2
    for i in range(size):
        if (i & c_mask) != 0:
            j = i ^ t_mask
            out_ref[i] = state[j]
    assert np.allclose(out_vec, out_ref)


def test_quantum_state_backend_default():
    qs = QuantumState.zero(2)
    qs.apply_single_qubit(H, 0)
    qs.apply_cnot(0, 1)
    probs = (qs.state.real ** 2 + qs.state.imag ** 2)
    assert np.isclose(probs.sum(), 1.0)


def test_batch_gate_equivalence():
    qs1 = QuantumState.zero(1)
    qs2 = QuantumState.zero(1)
    gates = [H, Z, H]
    for g in gates:
        qs1.apply_single_qubit(g, 0)
    qs2.apply_single_qubit_batch(gates, 0)
    assert np.allclose(qs1.state, qs2.state)
