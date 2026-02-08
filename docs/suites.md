# Unified Test Harness (run-suite)

The `run-suite` command is a single entrypoint that runs OND/ODD analysis together with external batteries and produces a unified, audit‑friendly bundle of artifacts.

## Command

```bash
ond-random run-suite --suite ond,nist,practrand,testu01,ea90b --out data/reports/run_suite
```

Use `--mode quick` (default) for fast runs and `--mode full` for larger samples. Missing external binaries are reported as `skipped` without failing the run.

## Output layout

```
data/reports/run_suite/
  metadata.json
  results.json
  artifacts/
    ond/
      observations.jsonl
      ond_art_report.json
    nist/
      nist_bits.bin
      nist_command.log
    testu01/
      testu01_bytes.bin
      testu01_command.log
    practrand/
      practrand.log
    ea90b/
      ea_symbols_8b.bin
      ea90b.log
```

## Results schema (summary)

`results.json` contains:

- `summary.overall`: `ok` | `partial` | `error`
- `summary.counts`: status counts (`ok`, `prepared`, `skipped`, `error`)
- `suites.<name>`: per‑suite summary and artifact paths

`metadata.json` contains:

- run provenance (timestamps, version, platform)
- RNG configuration used for generation
- full CLI arguments (for reproducibility)

Schema: `schemas/run_suite_metadata.schema.json` (validated in CI).

## External suite notes

The external batteries are optional:

- `nist` and `testu01` always generate input files and can optionally run a command via `--nist-command` / `--testu01-command` (use `{input}` placeholder).
- `practrand` runs `RNG_test` if found in `PATH` (or via `--practrand-cmd`).
- `ea90b` runs NIST EntropyAssessment if `ea_non_iid` / `ea_iid` is available (or via `--ea-path`).

Installation notes for external batteries live in `runners/README.md`.
