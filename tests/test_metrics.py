import numpy as np

from ond_random.ond.metrics import compute_profile


def test_profile_range():
    rng = np.random.default_rng(0)
    U = rng.integers(0, 2**32, size=(2000, 4), dtype=np.uint64)
    profile = compute_profile(U, modulus=2**32, branch_bins=None, branch_mode="raw")
    assert 0.0 <= profile.h_rank <= 1.0
    assert 0.0 <= profile.h_sub <= 1.0
    assert 0.0 <= profile.h_branch <= 1.0
