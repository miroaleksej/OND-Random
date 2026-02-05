# ODD/OND-ART Audit — Candidate Data Sources (OND-Random)

## Summary
- Total files scanned: **76**
- Confirmed observation sources: **30**
- Need extra parameters (e.g., curve order): **0**
- Derived reports/registries (not raw observations): **21**
- Not observation sources: **23**
- Errors: **0**

## Method
- Parsed numeric files (CSV/NPY/NPZ/JSONL/LOG) and computed basic statistics.
- Confirmed sources if numeric parsing succeeded and sample count > 0.
- Flagged sources that require domain parameters (e.g., ECDSA curve order).
- Non-observation JSON files (schemas/reports/registries) are excluded from raw-data confirmation.

## Detailed audit
### audit/verification/IsogenyGuard-SDK_data.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=ecdsa-secp256k1-rsz-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [200, 4], invalid_count=0

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

### data/benchmarks/I-ondmax.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=I-ondmax-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.162e+09, std=1.252e+09, min=3.613e+05, max=4.295e+09

### data/benchmarks/II-lcg.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=II-lcg-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.155e+09, std=1.231e+09, min=1.013e+05, max=4.295e+09

### data/benchmarks/II-xorshift.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=II-xorshift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.14e+09, std=1.235e+09, min=0, max=4.295e+09

### data/benchmarks/III-bounded.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=III-bounded-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2025, std=1187, min=0, max=4095

### data/benchmarks/IV-masked.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=IV-masked-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=1.608e+09, std=1.198e+09, min=0, max=3.234e+09

### data/benchmarks/Q-drift.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=Q-drift-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.545e+09, std=1.917e+09, min=0, max=4.295e+09

### data/benchmarks/Q-ideal.npz
- Status: **confirmed**
- Kind: `npz`
- π suggestion: `pi_id=Q-ideal-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Array `U` shape=[10000, 4], dtype=uint64
  - overall: mean=2.151e+09, std=1.247e+09, min=1.094e+06, max=4.293e+09

### reports/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=benchmark-ondmax-r4`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 4}`
- Observations shape: [10000, 4], invalid_count=0

### audit/verification/OND-Random_data_quantum_grover_measurements.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=grover-measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Observations shape: [2048, 1], invalid_count=0

### data/quantum/grover_measurements.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=grover-measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Series shape=[2048, 1], dtype=float64
  - overall: mean=58.8433, std=52.9669, min=0, max=252

### audit/verification/OND-Random_data_quantum_shor_measurements.csv/observations.jsonl
- Status: **confirmed**
- Kind: `observations`
- π suggestion: `pi_id=shor-measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Observations shape: [2048, 1], invalid_count=0

### data/quantum/shor_measurements.csv
- Status: **confirmed**
- Kind: `csv`
- π suggestion: `pi_id=shor-measurements-v1`, `pi_version=1.0.0`, `obs_space={'type': 'R^d', 'd': 1}`
- Series shape=[2048, 1], dtype=float64
  - overall: mean=95.875, std=72.1664, min=0, max=192

## Fix audit (need vs no‑need)
- **Needs parameters:** none (ECDSA curve order resolved with secp256k1).
- **Errors:** none.
- **Validation:** all generated baseline reports pass schema + invariants; small‑N sources are tagged `spec.profile=dev`.
- **Action items:** none at this time.

## Conclusions
- The majority of numeric sources are **ODD-ready** (CSV/NPZ/JSONL/log‑derived series).
- ECDSA hex data in this repo is **usable**, with curve order set to secp256k1.
- Schema/report JSON files are **not** raw observation sources and should not be treated as π inputs.
