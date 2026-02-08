# External Suite Runners

This folder documents how to install and run external batteries with `run-suite`.

## PractRand

1. Build or install PractRand (binary `RNG_test`).
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite practrand --practrand-cmd RNG_test --out data/reports/run_suite
```

## NIST STS (SP 800‑22)

1. Install NIST STS and identify the command you use to run tests.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite nist --nist-command "/path/to/assess {input}" --out data/reports/run_suite
```

## TestU01

1. Build TestU01 and provide a command/script that consumes raw bytes.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite testu01 --testu01-command "/path/to/your_harness {input}" --out data/reports/run_suite
```

## NIST EntropyAssessment (SP 800‑90B)

1. Build the EntropyAssessment tool and make `ea_non_iid` / `ea_iid` available.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite ea90b --ea-path /path/to/ea_non_iid --out data/reports/run_suite
```
