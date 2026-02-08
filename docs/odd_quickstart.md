# ODD Quickstart

This is the shortest path from raw artifacts → observations → OND‑ART report.

## 1) Export observations.jsonl

```bash
ond-random obs-export \
  --input your_data.csv --input-format csv --columns a,b,c \
  --pi-id my-system-v1 --pi-version 1.0.0 \
  --pi-registry docs/pi_registry.json --pi-registry-mode add \
  --out observations.jsonl
```

Tip: use `--pi-registry` with `check`/`add` to prevent `pi_spec_hash` drift.
Provenance (`commit`, `platform`, `generator_id`, `profile_id`) is included automatically.

## 2) Generate baseline report (one‑time)

```bash
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-observations observations.jsonl \
  --out reports/baseline_report.json \
  --protocol custom --scheme custom \
  --baseline-policy docs/baseline_policy.json \
  --bootstrap-samples 200
```

Optional OND/TDA topology channel (raw-only; requires `ripser`):

```bash
pip install "ond-random[tda]"
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-observations observations.jsonl \
  --out reports/baseline_report.json \
  --topology on --topology-mode both --topology-maxdim 2
```

Optional orbit‑spectrum channel (ks1/ks2; **Z_mod_m with 2D observations**):

```bash
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-observations observations.jsonl \
  --out reports/baseline_report.json \
  --orbit-spectrum on --orbit-topk 8
```

## 3) Regression report (per build/PR)

```bash
ond-random odd-report \
  --observations observations.jsonl \
  --baseline-report reports/baseline_report.json \
  --out reports/ond_art_report.json
```

Reports include `spec.profile` and `spec.x-method_version` (override with `--profile` / `--method-version`).
Spec/schema versioning: see `docs/ODD_VERSIONING.md`.

## 4) Validate in CI

Schema validation:

```bash
PYTHONPATH=. python scripts/validate_odd_artifacts.py \
  --observations observations.jsonl \
  --ond-art-report reports/ond_art_report.json
```

Or install the spec package and use the CLI:

```bash
pip install -e ./ond-odd-spec
ond-odd-validate --observations observations.jsonl --ond-art-report reports/ond_art_report.json
```
