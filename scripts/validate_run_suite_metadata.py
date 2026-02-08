from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True, help="path to metadata.json")
    parser.add_argument("--schema", default="schemas/run_suite_metadata.schema.json")
    args = parser.parse_args()

    meta_path = Path(args.metadata)
    schema_path = Path(args.schema)
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(metadata), key=lambda e: e.path)
    if errors:
        for err in errors:
            path = ".".join(str(p) for p in err.path) or "<root>"
            print(f"{path}: {err.message}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
