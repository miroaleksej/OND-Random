from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    dist = Path("dist")
    if not dist.exists():
        raise SystemExit("dist/ not found; run: python -m build")
    artifacts = sorted(p for p in dist.iterdir() if p.is_file())
    manifest = []
    for p in artifacts:
        manifest.append(
            {
                "file": p.name,
                "size": p.stat().st_size,
                "sha256": sha256_file(p),
            }
        )

    (dist / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    lines = [f"{item['sha256']}  {item['file']}" for item in manifest]
    (dist / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
