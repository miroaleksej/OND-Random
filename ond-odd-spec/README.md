# ond-odd-spec

Lightweight package with **ODD/OND‑ART JSON Schemas** and a validator CLI.

## Install (local)

```bash
pip install -e ./ond-odd-spec
```

## Validate artifacts

```bash
ond-odd-validate \
  --observations observations.jsonl \
  --ond-art-report reports/ond_art_report.json
```

### Validate profiles

```bash
ond-odd-validate \
  --profile data/benchmarks/large/I-ondmax.json \
  --profile data/reports/benchmark_profiles.json \
  --reference-profiles data/benchmarks/reference_profiles.json
```
