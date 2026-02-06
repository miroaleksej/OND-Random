import numpy as np

from ond_random.ond.orbit_spectrum import compute_orbit_spectrum, normalize_orbit_config


def test_orbit_spectrum_t0():
    n = 101
    U = np.array([[i, (2 * i) % n] for i in range(12)], dtype=int)
    obs_space = {"type": "Z_mod_m", "modulus": n}
    cfg = normalize_orbit_config({"enabled": True}, profile="dev")
    res = compute_orbit_spectrum(U, obs_space, cfg)
    assert res["status"] == "ok"
    assert res["summary"]["type"] == "T0"
    assert res["summary"]["unique_classes"] == 1
    sig = res["signature"]
    assert len(sig["vector"]) == len(sig["labels"])


def test_orbit_spectrum_t1():
    n = 97
    U = [(0, 0)]
    for i in range(1, 12):
        if i % 2 == 1:
            step = (1, 0)
        else:
            step = (0, 1)
        last = U[-1]
        U.append(((last[0] + step[0]) % n, (last[1] + step[1]) % n))
    U = np.array(U, dtype=int)
    obs_space = {"type": "Z_mod_m", "modulus": n}
    cfg = normalize_orbit_config({"enabled": True}, profile="dev")
    res = compute_orbit_spectrum(U, obs_space, cfg)
    assert res["status"] == "ok"
    assert res["summary"]["type"] == "T1"
    assert res["summary"]["unique_classes"] == 2
    assert res["information_bound_bits"] > 0


def test_orbit_spectrum_skips_non_modular():
    U = np.random.default_rng(0).normal(size=(10, 2))
    obs_space = {"type": "R^d", "d": 2}
    cfg = normalize_orbit_config({"enabled": True}, profile="dev")
    res = compute_orbit_spectrum(U, obs_space, cfg)
    assert res["status"] == "skipped"
