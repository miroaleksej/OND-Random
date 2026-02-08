# Full System Audit — OND-Random

- Audit timestamp (UTC): `2026-02-08T17:10:00Z`
- Repo head during audit: `83556cbd0b24ca1ba619b5c20f6888cf5a204fb0`
- Scope: full module/runtime audit + competitor comparison with refreshed large external artifacts.

## Executive Summary
- Functional baseline is healthy: `pytest` passes (`73 passed`), validators pass, CLI smoke checks pass.
- P1-002 is now fully closed on artifact completeness:
  - `lcg`, `xorshift`, and `quantum` now all have full large artifacts for PractRand/NIST/TestU01 FIPS.
- External coverage status is now `ok`:
  - `missing_targets=[]`
  - `partial_targets=[]`
  - `target_coverage_ratio=1.0`
  - `full_target_coverage_ratio=1.0`

## Runtime Verification Matrix
- `pytest -q`: `PASS` (`73` passed).
- `validate_extractor_spec.py` (ondmax/toeplitz): `PASS`.
- `validate_run_suite_metadata.py`: `PASS`.
- `validate_odd_artifacts.py`: `PASS`.
- `python -m py_compile scripts/*.py`: `PASS`.
- `scripts/check_external_coverage.py`: `PASS` (`status=ok`, details below).

## Competitor Benchmark Matrix

| RNG | Quick OND status | Large PractRand | Large NIST STS | Large TestU01 FIPS | External channel level |
| --- | --- | --- | --- | --- | --- |
| `ondmax` | `ok` | no anomalies @1GB | stable/passing profile | pass | `full` |
| `system` | `ok` | no anomalies @1GB | stable/passing profile | pass | `full` |
| `chacha20` | `ok` | no anomalies @1GB (seeds 1–3) | stable/passing profile | pass | `full` |
| `lcg` | `ok` | multiple FAIL classes @1GB | severe failures in legacy STS profile | pass | `full` |
| `xorshift` | `ok` | no anomalies @1GB | severe failures in legacy STS profile | **fail** (longest run) | `full` |
| `quantum` | `ok` | multiple FAIL/suspicious @1GB | severe failures in legacy STS profile | pass | `full` |

## External Coverage Status
- Source: `data/reports/external/large_coverage.json`
- `status`: `ok`
- `coverage_ratio`: `1.0`
- `full_target_coverage_ratio`: `1.0`
- `target_coverage_ratio`: `1.0`
- `missing_targets`: `[]`
- `partial_targets`: `[]`

## Findings (Prioritized)
- `P1-002` closed: all target generators now have required large external artifacts for comparator matrix.
- `P1-new`: benchmark comparability risk across NIST implementations.
  - Existing repo uses legacy STS profile (`sts_legacy_fft`) rather than the earlier `assess` style report.
  - Results are internally consistent and reproducible here, but should be labeled profile-specific.

## Comparative Verdict
- Verdict: `no_clear_global_winner`.
- Strongest overall external posture remains `ondmax/system/chacha20`.
- `lcg` is clearly weak on PractRand and STS in this run profile.
- `xorshift` is mixed: PractRand clean, STS severe failures, and FIPS fail case.
- `quantum` now has full large evidence and also fails strongly on PractRand and STS in this run profile.

## Repro Commands
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/check_external_coverage.py --root data/reports/external/large --out data/reports/external/large_coverage.json`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/external_rng_tests.py practrand --rng lcg --total-bytes 1073741824 --practrand-cmd /tmp/ond_tools/PractRand/RNG_test --practrand-args-str "-tlmin 1GB -tlmax 1GB" > data/reports/external/large/practrand/lcg_1gb.log`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/external_rng_tests.py testu01 --rng xorshift --bytes 268435456 --out /tmp/ond_tools/rng_data/testu01_xorshift_256.bin`
