from ond_random.protocols.ecdsa_synth import SECP256K1, public_key_from_private, synthetic_ecdsa_signature


def test_synthetic_ecdsa_bijection():
    curve = SECP256K1
    Q = public_key_from_private(5, curve)
    ur = 123456789
    uz = 987654321
    sig, z, R = synthetic_ecdsa_signature(ur, uz, Q, curve)

    # Recover u_r and u_z from (r, s, z)
    r = sig.r
    s = sig.s
    inv_s = pow(s, -1, curve.n)
    u_r_rec = (r * inv_s) % curve.n
    u_z_rec = (z * inv_s) % curve.n

    assert u_r_rec == ur % curve.n
    assert u_z_rec == uz % curve.n
    assert r == R.x % curve.n
