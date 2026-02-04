# Release प्रक्रिया

## Tagging
Use semantic version tags:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Automated pipeline
The GitHub Actions workflow `.github/workflows/release.yml` will:
- build sdist + wheel
- generate MANIFEST.json + SHA256SUMS
- sign artifacts using Sigstore
- publish a GitHub Release with signed artifacts

## Verification
Download artifacts and verify signatures using Sigstore:

```bash
sigstore verify identity \
  --cert-identity "https://github.com/<org>/<repo>/.github/workflows/release.yml@refs/tags/v0.1.0" \
  --cert-oidc-issuer "https://token.actions.githubusercontent.com" \
  dist/<artifact>

Verify hashes:

```bash
python scripts/verify_manifest.py
```
```
