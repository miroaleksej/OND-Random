# Manual — Role-based Command Checklist

This checklist groups **executable commands** by role. Use the same venv setup as in README.

---

## Role: RNG Evaluation

**Quick sanity (generate + profile)**

```bash
ond-random gen --rng ondmax --bits 256 --hex
ond-random profile --rng ondmax --samples 10000 --dimension 4 --word-bits 32 --modulus
```

**Profile from file (ODD / black-box inputs)**

```bash
ond-random profile-file --input vqe_noisy.csv --input-format csv --column energy --embed-dim 6 --branch-mode delta
ond-random profile-file --input tad_lhc.log --input-format text --regex "Event distribution: min=[0-9.]+, max=([0-9.]+), mean=" --embed-dim 4 --branch-mode delta
ond-random profile-file --input data.csv --input-format csv --ecdsa-rsz \
  --ecdsa-n 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141 \
  --modulus-embedding torus --branch-mode delta
```

**Benchmarks + quality report**

```bash
PYTHONPATH=. python scripts/generate_benchmarks.py --samples 10000 --dimension 4 --word-bits 32 --modulus
PYTHONPATH=. python scripts/quality_report.py
```

**Accuracy gate (numeric validation vs analytic)**

```bash
PYTHONPATH=. python scripts/accuracy_report.py --thresholds docs/accuracy_thresholds.json --out data/reports/accuracy_report.json
```

**Large-sample SLA regression**

```bash
PYTHONPATH=. python scripts/sla_regression.py --config docs/large_sample_sla.json --out data/reports/sla_regression.json
```

---

## Role: ODD Audit (candidate discovery)

**Export observations.jsonl**

```bash
ond-random obs-export \
  --input your_data.csv --input-format csv --columns a,b,c \
  --pi-id my-system-v1 --pi-version 1.0.0 \
  --pi-registry docs/pi_registry.json --pi-registry-mode add \
  --out observations.jsonl
```

**Build baseline (one-time)**

```bash
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-observations observations.jsonl \
  --out reports/baseline_report.json \
  --protocol custom --scheme custom \
  --baseline-policy docs/baseline_policy.json \
  --bootstrap-samples 200
```

**Regression (per build / PR)**

```bash
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-report reports/baseline_report.json \
  --out reports/ond_art_report.json
```

**Validate reports (CI equivalent)**

```bash
ond-art-validate --help   # if installed via OND-ART CI Pack
```

---

## Role: Quantum Checks

**Grover / Shor**

```bash
ond-random grover --items 100000 --target 42424 --shots 100
ond-random shor --N 15 --a 2 --shots 200
ond-random shor --N 15 --a 2 --shots 200 --gamma1 0.05 --gamma-phi 0.02
```

**Lindblad / trajectories validation**

```bash
PYTHONPATH=. python scripts/numeric_validation.py
PYTHONPATH=. python scripts/trajectories_report.py
```

**Shor noise report**

```bash
PYTHONPATH=. python scripts/shor_noise_report.py --shots 50 --trials 50 --gamma1 0.05 --gamma-phi 0.02
```

---

## Role: External Test Batteries

**PractRand (stream RNG into RNG_test)**

```bash
PYTHONPATH=. python scripts/external_rng_tests.py practrand --rng ondmax --total-bytes 1000000
```

**NIST STS (prepare bitstream; run STS separately)**

```bash
PYTHONPATH=. python scripts/external_rng_tests.py nist-sts --rng ondmax --bits 1000000 --format byte
```

**TestU01 (prepare raw bytes; run your harness)**

```bash
PYTHONPATH=. python scripts/external_rng_tests.py testu01 --rng ondmax --bytes 1000000
```

---

## Role: Full Pipeline (end-to-end)

```bash
PYTHONPATH=. python scripts/run_pipeline.py --samples 10000 --dimension 4 --word-bits 32 --branch-mode delta
PYTHONPATH=. python scripts/accuracy_report.py --thresholds docs/accuracy_thresholds.json --out data/reports/accuracy_report.json
PYTHONPATH=. python scripts/sla_regression.py --config docs/large_sample_sla.json --out data/reports/sla_regression.json
```

**What each command produces**

- `run_pipeline.py`  
  Writes a full suite of reports and a summary:
  - `data/reports/pipeline_summary.json`
  - `data/reports/benchmark_profiles.json`
  - `data/reports/quality_report.json`
  - `data/reports/numeric_validation.json`
  - `data/reports/shor_noise_report.json`
  - `data/reports/trajectories_vs_lindblad.json`
  - `data/reports/system_report.json` and `data/reports/system_report.md`
  - plus updated benchmark artifacts under `data/benchmarks/`

- `accuracy_report.py`  
  Computes numeric accuracy vs analytic baselines and writes:
  - `data/reports/accuracy_report.json` (PASS/FAIL + metrics + thresholds)

- `sla_regression.py`  
  Runs large-sample SLA regression against benchmark profiles and writes:
  - `data/reports/sla_regression.json` (PASS/FAIL + per-case diffs)
