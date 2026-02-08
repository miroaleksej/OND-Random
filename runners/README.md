# External Suite Runners

This folder documents how to install and run external batteries with `run-suite`.

## PractRand

1. Build or install PractRand (binary `RNG_test`).
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite practrand --practrand-cmd RNG_test --out data/reports/run_suite
```

Container runner:

```bash
PYTHONPATH=. python scripts/external_rng_tests.py export --rng ondmax --bytes 1000000 --out data/reports/rng_bytes.bin
docker build -t ond-practrand runners/containers/practrand
docker run --rm -v "$PWD:/work" -w /work ond-practrand data/reports/rng_bytes.bin
```

## NIST STS (SP 800‑22)

1. Install NIST STS and identify the command you use to run tests.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite nist --nist-command "/path/to/assess {input}" --out data/reports/run_suite
```

Container runner (expects STS build mounted at `/opt/nist-sts`):

```bash
docker build -t ond-nist runners/containers/nist
docker run --rm -v "$PWD:/work" -v /path/to/sts:/opt/nist-sts -w /work ond-nist data/reports/run_suite/artifacts/nist/nist_bits.bin
```

## TestU01

1. Build TestU01 and provide a command/script that consumes raw bytes.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite testu01 --testu01-command "/path/to/your_harness {input}" --out data/reports/run_suite
```

Container runner:

```bash
docker build -t ond-testu01 runners/containers/testu01
docker run --rm -v "$PWD:/work" -w /work ond-testu01 rabbit data/reports/run_suite/artifacts/testu01/testu01_bytes.bin
```

## NIST EntropyAssessment (SP 800‑90B)

1. Build the EntropyAssessment tool and make `ea_non_iid` / `ea_iid` available.
2. Run:

```bash
PYTHONPATH=. python -m ond_random.cli run-suite --suite ea90b --ea-path /path/to/ea_non_iid --out data/reports/run_suite
```
