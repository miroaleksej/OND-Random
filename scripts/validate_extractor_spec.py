from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="path to extractor spec JSON")
    parser.add_argument("--schema", default="schemas/extractor_spec.schema.json")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    schema_path = Path(args.schema)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(spec), key=lambda e: e.path)
    if errors:
        for err in errors:
            path = ".".join(str(p) for p in err.path) or "<root>"
            print(f"{path}: {err.message}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
