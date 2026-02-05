import math

import numpy as np

from ond_random.ond.embedding import delay_embed_series, torus_embed_modular, unit_scale_modular
from ond_random.ond.fileio import (
    load_csv_matrix,
    load_csv_series,
    load_ecdsa_rsz_csv,
    load_text_series_regex,
    parse_int_auto,
)


def test_delay_embed_series_shape_and_values():
    series = np.arange(10, dtype=float)
    U = delay_embed_series(series, embed_dim=3, delay=2, stride=1)
    assert U.shape == (6, 3)
    assert np.allclose(U[0], [0.0, 2.0, 4.0])
    assert np.allclose(U[1], [1.0, 3.0, 5.0])


def test_unit_scale_modular_range():
    n = 101
    U = np.array([[0, 100], [50, 25]], dtype=object)
    X = unit_scale_modular(U, modulus=n)
    assert X.shape == (2, 2)
    assert np.all((0.0 <= X) & (X < 1.0))
    assert math.isclose(X[0, 0], 0.0)
    assert math.isclose(X[0, 1], 100 / n)


def test_torus_embed_modular_unit_circle():
    n = 101
    U = np.array([[0, 25], [50, 75]], dtype=object)
    X = torus_embed_modular(U, modulus=n)
    assert X.shape == (2, 4)
    # Each (cos, sin) pair has norm ~ 1
    for i in range(X.shape[0]):
        for j in range(0, X.shape[1], 2):
            r = math.hypot(float(X[i, j]), float(X[i, j + 1]))
            assert abs(r - 1.0) < 1e-9


def test_load_csv_matrix_and_series(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    M = load_csv_matrix(str(p), columns=["a", "c"])
    assert M.shape == (2, 2)
    assert np.allclose(M, [[1.0, 3.0], [4.0, 6.0]])

    s = load_csv_series(str(p), column="b")
    assert s.shape == (2,)
    assert np.allclose(s, [2.0, 5.0])


def test_load_text_series_regex(tmp_path):
    p = tmp_path / "log.txt"
    p.write_text("x=1.25\nskip\nx=2.5\n", encoding="utf-8")
    s = load_text_series_regex(str(p), pattern=r"x=([0-9.]+)")
    assert np.allclose(s, [1.25, 2.5])


def test_load_ecdsa_rsz_csv_small_modulus(tmp_path):
    n = 10177
    p = tmp_path / "sig.csv"
    p.write_text("r,s,z\n1234,5678,42\n", encoding="utf-8")
    U = load_ecdsa_rsz_csv(str(p), n=n)
    assert U.shape == (1, 2)
    inv_s = pow(5678, -1, n)
    assert int(U[0, 0]) == (1234 * inv_s) % n
    assert int(U[0, 1]) == (42 * inv_s) % n


def test_parse_int_auto_hex():
    assert parse_int_auto("0x10") == 16
    assert parse_int_auto("ff") == 255

