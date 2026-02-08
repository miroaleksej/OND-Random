# ODD / OND‑ART Versioning & Compatibility

This document defines how we version **specs** and **schemas**, and how we handle compatibility.

## Fields

### `spec_version`
The version of the **ODD/OND‑ART specification** that defines semantics and required fields.

### `schema_version`
The version of the **JSON schema** used for validation.

Both values are carried in:
- `observations.jsonl` → `meta.spec.spec_version` / `meta.spec.schema_version`
- `ond_art_report.json` → `spec.spec_version` / `spec.schema_version`

Current versions:
- ODD‑OBS: `spec_version = "0.1"`, `schema_version = "0.1"`
- OND‑ART: `spec_version = "0.2"`, `schema_version = "0.2"`

## Compatibility policy

We follow a SemVer‑style rule for both `spec_version` and `schema_version`:

- **PATCH**: clarification or tightening that does not break existing artifacts.
- **MINOR**: backward‑compatible additions (new optional fields).
- **MAJOR**: breaking changes (field removed/renamed/semantics changed).

## Migration rules

When a **MAJOR** bump happens:

1. Provide a migration note in the release.
2. Add a `scripts/migrate_odd_artifacts.py` (or similar) with:
   - input version
   - output version
   - deterministic field mapping
3. Keep the validator compatible with the previous **major** for one release cycle.

## Migration tool

Use the built‑in migration script to fill missing `spec_version` / `schema_version` fields:

```bash
PYTHONPATH=. python scripts/migrate_odd_artifacts.py \
  --observations observations.jsonl \
  --ond-art-report reports/ond_art_report.json \
  --out-dir migrated/
```

In‑place update:

```bash
PYTHONPATH=. python scripts/migrate_odd_artifacts.py \
  --observations observations.jsonl \
  --ond-art-report reports/ond_art_report.json \
  --in-place
```

## Validator behavior

The validator:
- accepts older artifacts when missing newly added optional fields;
- rejects missing required fields for the declared `schema_version`.

This is the default contract for CI gates.

## Required provenance fields

OND‑ART reports now require:
- `provenance.commit`
- `provenance.platform`
- `provenance.generator_id`
- `provenance.profile_id`

Use the migration tool to backfill these fields in existing reports.

## Backward‑compat mode

If you need to accept older **major** versions during a transition window:

```bash
ond-odd-validate \
  --allow-older-majors \
  --observations observations.jsonl \
  --ond-art-report reports/ond_art_report.json
```
