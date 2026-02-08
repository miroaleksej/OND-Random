from ond_random.rng.extractor import toeplitz_hash


def _bytes_to_bits(data: bytes) -> list[int]:
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_from_bytes(data: bytes, count: int) -> list[int]:
    bits = _bytes_to_bits(data)
    return bits[:count]


def _naive_toeplitz(input_bits: list[int], seed_bits: list[int], output_bits: int) -> list[int]:
    n = len(input_bits)
    required = n + output_bits - 1
    tprime = seed_bits[:required]
    out = []
    for i in range(output_bits):
        start = (output_bits - 1) - i
        acc = 0
        for j in range(n):
            acc ^= input_bits[j] & tprime[start + j]
        out.append(acc)
    return out


def test_toeplitz_hash_matches_naive():
    input_bytes = bytes([0b10110010])
    seed_bytes = bytes([0b11001010, 0b01110100])
    output_bits = 6
    expected_bits = _naive_toeplitz(_bytes_to_bits(input_bytes), _bytes_to_bits(seed_bytes), output_bits)
    out_bytes = toeplitz_hash(input_bytes, seed_bytes, output_bits)
    got_bits = _bits_from_bytes(out_bytes, output_bits)
    assert got_bits == expected_bits
