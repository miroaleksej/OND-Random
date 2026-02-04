import numpy as np

from ond_random.protocols.ecdsa import ECDSAObservation, ECDSAParams, ECDSASignature
from ond_random.protocols.schnorr import SchnorrObservation, SchnorrParams, SchnorrSignature
from ond_random.protocols.pq import LatticeObservation, LatticeParams, LatticeSignature


def test_ecdsa_observation_urz():
    n = 10177
    params = ECDSAParams(n=n, hash_name="sha256")
    obs = ECDSAObservation(params, mode="urz")
    sig = ECDSASignature(r=1234, s=5678)
    U = obs.observe(sig, message=b"msg")
    assert U.shape == (2,)
    # u_r and u_z are in [0, n)
    assert 0 <= U[0] < n
    assert 0 <= U[1] < n


def test_schnorr_observation_es():
    n = 10177
    params = SchnorrParams(n=n, hash_name="sha256")
    obs = SchnorrObservation(params, mode="es")
    sig = SchnorrSignature(r=2222, s=3333)
    U = obs.observe(sig, message=b"hello")
    assert U.shape == (2,)
    assert 0 <= U[0] < n
    assert 0 <= U[1] < n


def test_lattice_observation():
    params = LatticeParams(modulus=8380417, dimension=4, mode="z_mod_q")
    obs = LatticeObservation(params)
    sig = LatticeSignature(z=[1, 2, 3, 4, 5])
    U = obs.observe(sig)
    assert U.shape == (4,)
    assert np.all(U < params.modulus)
