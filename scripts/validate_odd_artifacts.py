from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> int:
    root = Path(__file__).resolve().parents[1]
    spec_root = root / "ond-odd-spec"
    if spec_root.exists():
        sys.path.insert(0, str(spec_root))
    try:
        from ond_odd_spec.cli import main
    except Exception as exc:
        print(f"Failed to import ond_odd_spec: {exc}")
        print("Install with: pip install -e ./ond-odd-spec")
        return 1
    return main()


if __name__ == "__main__":
    raise SystemExit(_bootstrap())
