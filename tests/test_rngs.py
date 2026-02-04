import os

from ond_random.rng.lcg import LCGRNG
from ond_random.rng.xorshift import XorShiftRNG
from ond_random.rng.chacha20 import ChaCha20RNG
from ond_random.rng.extractor import ONDMaxRNG
from ond_random.rng.system import SystemRNG


def test_lcg_deterministic():
    rng1 = LCGRNG(seed=123)
    rng2 = LCGRNG(seed=123)
    assert rng1.random_bytes(64) == rng2.random_bytes(64)


def test_xorshift_deterministic():
    rng1 = XorShiftRNG(1, 2)
    rng2 = XorShiftRNG(1, 2)
    assert rng1.random_bytes(64) == rng2.random_bytes(64)


def test_chacha20_reproducible():
    key = b"k" * 32
    rng1 = ChaCha20RNG(key=key)
    rng2 = ChaCha20RNG(key=key)
    assert rng1.random_bytes(128) == rng2.random_bytes(128)


def test_ondmax_length():
    rng = ONDMaxRNG(SystemRNG())
    out = rng.random_bytes(100)
    assert len(out) == 100
    # Should not be all-zero
    assert out != b"\x00" * 100


def test_random_bits_lengths():
    rng = ONDMaxRNG(SystemRNG())
    assert len(rng.random_bits(256)) == 32
    assert len(rng.random_bits(512)) == 64
    assert len(rng.random_bits(1024)) == 128
