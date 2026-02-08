# Release Guide

## Prerequisites
- Configure a PyPI Trusted Publisher for this repository/workflow:
  - publisher repo: `miroaleksej/OND-Random`
  - workflow: `.github/workflows/release.yml`
  - environment (optional): use your PyPI policy
- Ensure the target version in `pyproject.toml` is correct.

## Create a release tag
```bash
git tag v0.1.0
git push origin v0.1.0
```

## What the release workflow does
Workflow: `.github/workflows/release.yml`

1. Builds `sdist` and `wheel`.
2. Generates `dist/MANIFEST.json` and `dist/SHA256SUMS`.
3. Publishes to PyPI via Trusted Publishing (`pypa/gh-action-pypi-publish`).
4. Enables PyPI attestations (PEP 740 support in the publish action).
5. Creates a GitHub Release and uploads all `dist/*` artifacts.

## Manual rerun for an existing tag
Use `workflow_dispatch` and provide `tag` (for example `v0.1.0`).

## Verify artifacts
```bash
python scripts/verify_manifest.py
```

For installation checks:
```bash
python -m pip install ond-random==0.1.0
python -m ond_random.cli --help
```
