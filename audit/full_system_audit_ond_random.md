# Full System Audit — OND-Random (Post-P1 Fix)

- Audit timestamp (UTC): `2026-02-08T12:04:38Z`
- Repo head during audit: `ee02f37213b0aa290d3bc7a19048c66e780fab69`
- Scope: `OND-Random` only
- Runtime output root: `/tmp/ond_audit_run`

## Executive Summary
- P1 fixes are implemented and validated:
  1. `ond_art_report.json` no longer emits top-level `baseline: null` at runtime.
  2. Schema now accepts legacy `baseline: null` for backward compatibility.
  3. `run-suite` resolves git provenance from repository context even when `--out` is under `/tmp`.
- Verification status: `pytest` passed (`59/59`), smoke commands passed, validators passed.
- Competitor comparison section is unchanged methodologically and remains "no clear winner" across all channels with current local evidence.

## What Was Fixed (P1)

### 1) Baseline schema/runtime alignment
- Runtime change (`ond_random/ond/odd_report.py`):
  - top-level `baseline` is added only when computed as an object;
  - topology/orbit baseline fallback thresholds are always deterministic objects (`green/yellow/red`), never `null`.
- Schema change (`schemas/ond_art_report.schema.json` and `ond-odd-spec/.../ond_art_report.schema.json`):
  - baseline references now allow `object | null` for compatibility at:
    - top-level `baseline`,
    - `topology.baseline`,
    - `orbit_spectrum.baseline`.

### 2) `run-suite` git provenance in `/tmp`
- `ond_random/suites/run_suite.py` now resolves git context via candidate roots:
  - `Path.cwd()` → package root (`Path(__file__).resolve().parents[2]`) → `out_dir`.
- The resolved repo base is reused both for:
  - `metadata.json.git`,
  - OND observations provenance in suite mode.

## Verification Evidence

### Tests
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q`
- Result: `59 passed in 0.57s`

### Smoke and validators
- `obs-export` smoke: PASS
- `odd-report` smoke: PASS
- `run-suite --suite ond --mode quick`: PASS (`overall=ok`)
- `validate_odd_artifacts.py` on smoke report: PASS
- `validate_odd_artifacts.py` on run-suite report: PASS
- `validate_run_suite_metadata.py` on `/tmp/ond_audit_run/run_suite_quick/metadata.json`: PASS
- Observed metadata snippet confirms provenance fix:
  - `git.commit = ee02f37213b0aa290d3bc7a19048c66e780fab69`

## Current Findings (Open)

### P2
1. Some scripts remain weakly wired to docs/CI flows (operational discoverability gap):
   - `scripts/big_physics_test.py`
   - `scripts/evidence_report.py`
   - `scripts/generate_benchmarks.py`
   - `scripts/shor_batch.py`
   - `scripts/system_report.py`
   - `scripts/verify_manifest.py`
2. No committed canonical `run-suite` metadata fixture for static schema checks (validation currently demonstrated via dynamic generation).

## Competitor Comparison (Local Evidence, unchanged)
- Source set:
  - `external_batteries_summary.md`
  - `data/reports/evidence_report.json`
  - `data/reports/evidence_report.md`
- Verdict unchanged: **no strict global winner**.
  - External batteries (large): `ondmax/system/chacha20` are on-par.
  - OND distance channel: `quantum/chacha20/system` clustered; `lcg/xorshift` less stable across seeds.
  - Confidence remains medium due incomplete external-battery coverage for some generators.

## Updated Command Set (Repro)
```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m ond_random.cli obs-export --input data/benchmarks/Q-ideal.npz --input-format npz --npz-key U --pi-id audit-smoke-qideal --pi-version 1.0.0 --out /tmp/ond_audit_run/smoke/observations.jsonl
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m ond_random.cli odd-report --observations /tmp/ond_audit_run/smoke/observations.jsonl --out /tmp/ond_audit_run/smoke/ond_art_report.json --profile recommended
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m ond_random.cli run-suite --suite ond --mode quick --out /tmp/ond_audit_run/run_suite_quick
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/validate_odd_artifacts.py --observations /tmp/ond_audit_run/smoke/observations.jsonl --ond-art-report /tmp/ond_audit_run/smoke/ond_art_report.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/validate_odd_artifacts.py --observations /tmp/ond_audit_run/run_suite_quick/artifacts/ond/observations.jsonl --ond-art-report /tmp/ond_audit_run/run_suite_quick/artifacts/ond/ond_art_report.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python scripts/validate_run_suite_metadata.py --metadata /tmp/ond_audit_run/run_suite_quick/metadata.json
```
