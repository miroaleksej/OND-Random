from __future__ import annotations

import json
from pathlib import Path
import hashlib


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    dist = Path("dist")
    manifest_path = dist / "MANIFEST.json"
    if not manifest_path.exists():
        raise SystemExit("MANIFEST.json not found in dist/")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest:
        path = dist / item["file"]
        if not path.exists():
            raise SystemExit(f"missing artifact: {path.name}")
        digest = sha256_file(path)
        if digest != item["sha256"]:
            raise SystemExit(f"hash mismatch: {path.name}")
    print("manifest verification ok")


if __name__ == "__main__":
    main()
