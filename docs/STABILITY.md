# API Stability Policy

We follow semantic versioning (SemVer): `MAJOR.MINOR.PATCH`.

- **PATCH**: bug fixes, no API changes
- **MINOR**: backward-compatible additions
- **MAJOR**: breaking changes

Breaking changes require:
- Documented migration notes
- Deprecation period when feasible

Only the API surface in `docs/API.md` is guaranteed stable.
