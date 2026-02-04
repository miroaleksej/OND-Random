from ond_random.quantum.shor import shor_factor
from ond_random.rng.lcg import LCGRNG


def test_shor_15():
    rng = LCGRNG(seed=123)
    result = shor_factor(N=15, a=2, shots=20, rng=rng)
    assert result.factors is not None
    assert set(result.factors) == {3, 5}


def test_shor_21():
    rng = LCGRNG(seed=456)
    result = shor_factor(N=21, a=2, shots=30, rng=rng)
    assert result.factors is not None
    assert set(result.factors) == {3, 7}
