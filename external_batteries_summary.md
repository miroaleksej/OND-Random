# External Batteries Summary

Generated: 2026-02-08  
Artifacts: `data/reports/external/`

## Baseline run (64MB / 16 streams / 64MB)

### PractRand (RNG_test)
Config: `stdin64`, core test set, folding standard, `-tlmin 64MB -tlmax 64MB`.

| RNG | Seed | Result | Log |
| --- | --- | --- | --- |
| `ondmax` | — | No anomalies (177 tests) | `data/reports/external/practrand/ondmax.log` |
| `system` | — | No anomalies (177 tests) | `data/reports/external/practrand/system.log` |
| `chacha20` | 1 | **1 unusual** (Low4/64 Gap-16:B, p=7.6e-4) | `data/reports/external/practrand/chacha20_seed1.log` |
| `chacha20` | 2 | No anomalies (177 tests) | `data/reports/external/practrand/chacha20_seed2.log` |
| `chacha20` | 3 | No anomalies (177 tests) | `data/reports/external/practrand/chacha20_seed3.log` |

### NIST STS (SP 800-22)
Config: 16 bitstreams × 1,048,576 bits (ASCII input, STS legacy FFT build).

| RNG | Seed | Passed | Result |
| --- | --- | --- | --- |
| `ondmax` | — | **185/188** | `data/reports/external/nist/ondmax/result.txt` |
| `system` | — | **187/188** | `data/reports/external/nist/system/result.txt` |
| `chacha20` | 1 | **187/188** | `data/reports/external/nist/chacha20_seed1/result.txt` |
| `chacha20` | 2 | **187/188** | `data/reports/external/nist/chacha20_seed2/result.txt` |
| `chacha20` | 3 | **187/188** | `data/reports/external/nist/chacha20_seed3/result.txt` |

### TestU01 — Rabbit (file-based)
Config: `bbattery_RabbitFile`, `nb = 536,870,912` bits (64MB per RNG/seed).

| RNG | Seed | Status | Log |
| --- | --- | --- | --- |
| `ondmax` | — | Completed (see p-values) | `data/reports/external/testu01/ondmax_rabbit.txt` |
| `system` | — | Completed (see p-values) | `data/reports/external/testu01/system_rabbit.txt` |
| `chacha20` | 1 | Completed (see p-values) | `data/reports/external/testu01/chacha20_seed1_rabbit.txt` |
| `chacha20` | 2 | Completed (see p-values) | `data/reports/external/testu01/chacha20_seed2_rabbit.txt` |
| `chacha20` | 3 | Completed (see p-values) | `data/reports/external/testu01/chacha20_seed3_rabbit.txt` |

### TestU01 — FIPS 140-2 (file-based)
Config: `bbattery_FIPS_140_2File`, 20,000 bits from each file.

| RNG | Seed | Result | Log |
| --- | --- | --- | --- |
| `ondmax` | — | Pass | `data/reports/external/testu01/ondmax_fips.txt` |
| `system` | — | Pass | `data/reports/external/testu01/system_fips.txt` |
| `chacha20` | 1 | Pass | `data/reports/external/testu01/chacha20_seed1_fips.txt` |
| `chacha20` | 2 | Pass | `data/reports/external/testu01/chacha20_seed2_fips.txt` |
| `chacha20` | 3 | Pass | `data/reports/external/testu01/chacha20_seed3_fips.txt` |

### Notes
- NIST STS “Non-overlapping Template” is the only sub-test category with sporadic failures in these runs; see each `result.txt`.
- TestU01 SmallCrush/Crush/BigCrush were not run here (they require much larger inputs).

## Large run (1GB / 256 streams / 256MB)

### PractRand (RNG_test)
Config: `stdin64`, core test set, folding standard, `-tlmin 1GB -tlmax 1GB`.

| RNG | Seed | Result | Log |
| --- | --- | --- | --- |
| `ondmax` | — | No anomalies (243 tests) | `data/reports/external/large/practrand/ondmax_1gb.log` |
| `system` | — | No anomalies (243 tests) | `data/reports/external/large/practrand/system_1gb.log` |
| `chacha20` | 1 | No anomalies (243 tests) | `data/reports/external/large/practrand/chacha20_seed1_1gb.log` |
| `chacha20` | 2 | No anomalies (243 tests) | `data/reports/external/large/practrand/chacha20_seed2_1gb.log` |
| `chacha20` | 3 | No anomalies (243 tests) | `data/reports/external/large/practrand/chacha20_seed3_1gb.log` |
| `lcg` | — | **Multiple FAILs** (BCFN / Gap / BRank / TMFn classes) | `data/reports/external/large/practrand/lcg_1gb.log` |
| `xorshift` | — | No anomalies (243 tests) | `data/reports/external/large/practrand/xorshift_1gb.log` |
| `quantum` | — | **Multiple FAIL/suspicious at 1GB** | `data/reports/external/large/practrand/quantum_1gb.log` |

### NIST STS (SP 800-22)
Config: 256 bitstreams × 1,048,576 bits (ASCII input, STS legacy FFT build).

| RNG | Seed | Passed | Result |
| --- | --- | --- | --- |
| `ondmax` | — | **187/188** | `data/reports/external/large/nist/ondmax/result.txt` |
| `system` | — | **186/188** | `data/reports/external/large/nist/system/result.txt` |
| `chacha20` | 1 | **187/188** | `data/reports/external/large/nist/chacha20_seed1/result.txt` |
| `chacha20` | 2 | **188/188** | `data/reports/external/large/nist/chacha20_seed2/result.txt` |
| `chacha20` | 3 | **185/188** | `data/reports/external/large/nist/chacha20_seed3/result.txt` |
| `lcg` | — | **Severe failures** (many tests flagged) | `data/reports/external/large/nist/lcg/result.txt` |
| `xorshift` | — | **Severe failures** (many tests flagged) | `data/reports/external/large/nist/xorshift/result.txt` |
| `quantum` | — | **Severe failures** (many tests flagged) | `data/reports/external/large/nist/quantum/result.txt` |

### TestU01 — Rabbit (file-based)
Config: `bbattery_RabbitFile`, `nb = 2,147,483,648` bits (256MB per RNG/seed).

| RNG | Seed | Status | Log |
| --- | --- | --- | --- |
| `ondmax` | — | Completed (see p-values) | `data/reports/external/large/testu01/ondmax_rabbit.txt` |
| `system` | — | Completed (see p-values) | `data/reports/external/large/testu01/system_rabbit.txt` |
| `chacha20` | 1 | Completed (see p-values) | `data/reports/external/large/testu01/chacha20_seed1_rabbit.txt` |
| `chacha20` | 2 | Completed (see p-values) | `data/reports/external/large/testu01/chacha20_seed2_rabbit.txt` |
| `chacha20` | 3 | Completed (see p-values) | `data/reports/external/large/testu01/chacha20_seed3_rabbit.txt` |
| `lcg` | — | Completed (see p-values) | `data/reports/external/large/testu01/lcg_rabbit.txt` |
| `xorshift` | — | Completed (see p-values) | `data/reports/external/large/testu01/xorshift_rabbit.txt` |
| `quantum` | — | Completed (see p-values) | `data/reports/external/large/testu01/quantum_rabbit.txt` |

### TestU01 — FIPS 140-2 (file-based)
Config: `bbattery_FIPS_140_2File`, 20,000 bits from each file.

| RNG | Seed | Result | Log |
| --- | --- | --- | --- |
| `ondmax` | — | Pass | `data/reports/external/large/testu01/ondmax_fips.txt` |
| `system` | — | Pass | `data/reports/external/large/testu01/system_fips.txt` |
| `chacha20` | 1 | Pass | `data/reports/external/large/testu01/chacha20_seed1_fips.txt` |
| `chacha20` | 2 | Pass | `data/reports/external/large/testu01/chacha20_seed2_fips.txt` |
| `chacha20` | 3 | Pass | `data/reports/external/large/testu01/chacha20_seed3_fips.txt` |
| `lcg` | — | Pass | `data/reports/external/large/testu01/lcg_fips.txt` |
| `xorshift` | — | **Fail** (longest run of 0) | `data/reports/external/large/testu01/xorshift_fips.txt` |
| `quantum` | — | Pass | `data/reports/external/large/testu01/quantum_fips.txt` |

### Notes
- Coverage is now complete for all target generators in the large matrix (`ondmax/system/chacha20/lcg/xorshift/quantum`).
- `lcg` and `xorshift` fail strongly in STS legacy run profile used here.
- `quantum` is now measured on full large profile and also shows strong failures in PractRand and STS legacy profile.

### Conclusion (large run)
- PractRand: `ondmax/system/chacha20/xorshift` show no anomalies at 1GB, while `lcg` fails heavily.
- NIST STS (legacy FFT profile in this repo): `lcg/xorshift` show widespread failures under this run profile; `ondmax/system/chacha20` remain comparatively stronger.
- TestU01 FIPS: most generators pass, but `xorshift` has a fail case on longest run.
- Conclusion: there is still **no single global winner** across all channels; `lcg` and `quantum` are clearly weaker in this large-run profile, while `ondmax/system/chacha20` remain the strongest group.
