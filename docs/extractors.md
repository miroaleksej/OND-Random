# Extractors (ONDMax + Toeplitz)

OND‑Random includes two extractor paths:

- **ONDMaxRNG** (SHAKE256‑based, practical)
- **Toeplitz** (universal hashing, information‑theoretic)

## ONDMaxRNG

**Parameters**

- `seed_bytes`: number of bytes drawn from the source to seed the sponge.
- `reseed_interval`: bytes generated before re‑seeding from the source.
- `personalization`: domain separation string (default `OND-RANDOM-v1`).

**Usage**

```bash
ond-random extract --method ondmax --out-bytes 32 --hex
```

If `--input` is provided, the extractor is applied deterministically as:

```
SHAKE256(personalization || input_bytes)
```

## Toeplitz extractor

Toeplitz hashing implements a universal linear hash from `n` input bits to
`m` output bits, defined by a seed of `n + m − 1` bits.

**Parameters**

- `input_bytes`: input length (if sourcing from RNG).
- `out_bytes`: output length.
- `toeplitz_seed_hex` / `toeplitz_seed_bytes`: seed for the Toeplitz matrix.

**Usage**

```bash
ond-random extract --method toeplitz --out-bytes 32 --input-bytes 64 --hex
```

If `--input` is provided, it is used directly; otherwise input bytes are
drawn from the selected RNG.

## Comparison script

```bash
PYTHONPATH=. python scripts/extractor_comparison.py --output-bytes 100000
```

The report includes throughput and OND profiles for `raw`, `ondmax`,
and `toeplitz`.

## Conditioning component report (90B‑style)

This is a lightweight report that checks whether the observed min‑entropy
is sufficient for a given output length and security parameter.

```bash
PYTHONPATH=. python scripts/conditioning_report.py \
  --method toeplitz \
  --output-bits 256 \
  --epsilon 2.3283064365386963e-10 \
  --run-suite-results data/reports/run_suite/results.json
```

If you have a standalone EntropyAssessment report:

```bash
PYTHONPATH=. python scripts/conditioning_report.py \
  --method toeplitz \
  --output-bits 256 \
  --epsilon 2.3283064365386963e-10 \
  --ea-report data/reports/nist_entropy_report.json
```
