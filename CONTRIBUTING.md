# Contributing

Thanks for contributing to OND Random.

## Development setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Tests
```bash
PYTHONPATH=. python -m pytest -q
```

## Coding rules
- Keep RNG and OND metrics on **raw data** (no normalization)
- Avoid hidden parameters or implicit state
- Prefer deterministic behavior for tests

## Security issues
See `SECURITY.md` for reporting security vulnerabilities.
