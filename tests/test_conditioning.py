from ond_random.rng.conditioning import toeplitz_required_min_entropy


def test_toeplitz_required_min_entropy():
    epsilon = 2 ** -32
    required = toeplitz_required_min_entropy(256, epsilon)
    assert required == 320.0
