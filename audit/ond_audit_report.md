# ODD/OND-ART Audit — Candidate Data Sources

## Summary
- Total files scanned: **94**
- Confirmed observation sources: **35**
- Need extra parameters (e.g., curve order): **0**
- Derived reports/registries (not raw observations): **22**
- Not observation sources: **35**
- Errors: **0**

## Method
- Parsed numeric files (CSV/NPY/NPZ/JSONL/LOG) and computed basic statistics.
- Confirmed sources if numeric parsing succeeded and sample count > 0.
- Flagged sources that require domain parameters (e.g., ECDSA curve order).
- Non-observation JSON files (schemas/reports/registries) are excluded from raw-data confirmation.

## Detailed audit
### IsogenyGuard-SDK/data.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=ecdsa-secp256k1-rsz-v1`, `pi_version=1.0.0`, `obs_space={'type': 'Z_mod_m', 'modulus': 115792089237316195423570985008687907852837564279074904382605163141518161494337, 'd': 2}`
- Rows: 200, Columns: 3
  - r (hex): mean_bits=254.99, min_bits=247.0, max_bits=256.0
  - s (hex): mean_bits=254.79, min_bits=248.0, max_bits=256.0
  - z (hex): mean_bits=255.12, min_bits=250.0, max_bits=256.0

### Noisy-VQE-Benchmark-Rayon-scaling-/chi_40.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=chi_40-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Columns: max_bond, depth, chi_max, layer_ms
- Rows: 40, Columns: 4
  - max_bond: mean=24, std=8, min=16, max=32
  - depth: mean=52.5, std=28.83, min=5, max=100
  - chi_max: mean=24, std=8, min=16, max=32
  - layer_ms: mean=27.1, std=20.08, min=5.659, max=49.44

### Noisy-VQE-Benchmark-Rayon-scaling-/fid_12.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=fid_12-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 3}`
- Columns: chi, fidelity, one_minus_fidelity
- Rows: 4, Columns: 3
  - chi: mean=15, std=10.72, min=4, max=32
  - fidelity: mean=0.3912, std=0.3157, min=0.01555, max=0.8376
  - one_minus_fidelity: mean=0.6088, std=0.3157, min=0.1624, max=0.9844

### Noisy-VQE-Benchmark-Rayon-scaling-/fidelity_24.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=fidelity_24-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 3}`
- Columns: chi, fidelity, one_minus_fidelity
- Rows: 4, Columns: 3
  - chi: mean=15, std=10.72, min=4, max=32
  - fidelity: mean=4.345e-08, std=3.919e-08, min=2.476e-09, max=1.076e-07
  - one_minus_fidelity: mean=1, std=3.919e-08, min=1, max=1

### Noisy-VQE-Benchmark-Rayon-scaling-/fidelity_24_depth.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=fidelity_24_depth-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Columns: depth, chi, fidelity, one_minus_fidelity
- Rows: 60, Columns: 4
  - depth: mean=16, std=8.641, min=2, max=30
  - chi: mean=15, std=10.72, min=4, max=32
  - fidelity: mean=0.1426, std=0.3197, min=2.476e-09, max=1
  - one_minus_fidelity: mean=0.8574, std=0.3197, min=0, max=1

### Noisy-VQE-Benchmark-Rayon-scaling-/vqe_analytic.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=vqe_analytic-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Columns: theta, energy
- Rows: 201, Columns: 2
  - theta: mean=3.142, std=1.823, min=0, max=6.283
  - energy: mean=0.004975, std=0.7088, min=-1, max=1

### Noisy-VQE-Benchmark-Rayon-scaling-/vqe_noisy.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=vqe_noisy-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Columns: theta, energy
- Rows: 201, Columns: 2
  - theta: mean=3.142, std=1.823, min=0, max=6.283
  - energy: mean=0.002468, std=0.7021, min=-1, max=1

### Noisy-VQE-Benchmark-Rayon-scaling-/vqe_shots.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=vqe_shots-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Columns: theta, energy
- Rows: 61, Columns: 2
  - theta: mean=3.142, std=1.844, min=0, max=6.283
  - energy: mean=0.01836, std=0.7168, min=-1, max=1

### OND-Random/data/benchmarks/I-ondmax.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=I-ondmax-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.162e+09, std=1.252e+09, min=3.613e+05, max=4.295e+09

### OND-Random/data/benchmarks/II-lcg.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=II-lcg-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.155e+09, std=1.231e+09, min=1.013e+05, max=4.295e+09

### OND-Random/data/benchmarks/II-xorshift.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=II-xorshift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.14e+09, std=1.235e+09, min=0, max=4.295e+09

### OND-Random/data/benchmarks/III-bounded.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=III-bounded-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2025, std=1187, min=0, max=4095

### OND-Random/data/benchmarks/IV-masked.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=IV-masked-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=1.608e+09, std=1.198e+09, min=0, max=3.234e+09

### OND-Random/data/benchmarks/Q-drift.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=Q-drift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.545e+09, std=1.917e+09, min=0, max=4.295e+09

### OND-Random/data/benchmarks/Q-ideal.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=Q-ideal-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.151e+09, std=1.247e+09, min=1.094e+06, max=4.293e+09

### OND-Random/reports/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=benchmark-ondmax-r4`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### Topology-Guided-Empirical-Formula-Discovery-TGEFD-/examples/data/sample_measurements.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=sample_measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Columns: time, signal
- Rows: 10, Columns: 2
  - time: mean=0.45, std=0.2872, min=0, max=0.9
  - signal: mean=0.509, std=0.2898, min=0.12, max=1.02

### Unified-LHC-Framework/tad_lhc.log
- Status: **confirmed**
- Kind: `log`
- π suggestion: `pi_id=tad_lhc-event-mean-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Regex: `Event distribution: min=([0-9.]+), max=([0-9.]+), mean=([0-9.]+) (use mean)`
- Lines: 192, event windows: 28
  - mean stats: mean=0.005357, std=0.01238, min=0.001, max=0.05

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_chi_40.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=chi_40-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [40, 4], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_fid_12.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=fid_12-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 3}`
- Observations shape: [4, 3], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_fidelity_24.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=fidelity_24-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 3}`
- Observations shape: [4, 3], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_fidelity_24_depth.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=fidelity_24_depth-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [60, 4], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_vqe_analytic.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=vqe_analytic-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Observations shape: [201, 2], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_vqe_noisy.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=vqe_noisy-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Observations shape: [201, 2], invalid_count=0

### audit/verification/Noisy-VQE-Benchmark-Rayon-scaling-_vqe_shots.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=vqe_shots-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Observations shape: [61, 2], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_I-ondmax.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=I-ondmax-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_II-lcg.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=II-lcg-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_II-xorshift.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=II-xorshift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_III-bounded.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=III-bounded-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_IV-masked.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=IV-masked-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_Q-drift.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=Q-drift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_benchmarks_Q-ideal.npz/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=Q-ideal-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_reports_observations.jsonl/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=benchmark-ondmax-r4`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/Topology-Guided-Empirical-Formula-Discovery-TGEFD-_examples_data_sample_measurements.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=sample_measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 2}`
- Observations shape: [10, 2], invalid_count=0

### audit/verification/Unified-LHC-Framework_tad_lhc.log/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=tad_lhc-event-mean-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Observations shape: [28, 1], invalid_count=0

## Validation results
- OND-ART baseline report (`OND-Random/reports/baseline_report.json`) validated successfully with OND-ART CI Pack.
- Observations JSONL format checked via parser (`read_observations_jsonl`) during audit.

## Conclusions
- The majority of numeric sources are **ODD-ready** (CSV/NPZ/JSONL/log‑derived series).
- ECDSA hex data (`IsogenyGuard-SDK/data.csv`) is **usable**, and its curve order is set to secp256k1.
- Schema/report JSON files are **not** raw observation sources and should not be treated as π inputs.
- Baseline report now passes CI validation; this can gate PRs reliably for OND‑Random.
