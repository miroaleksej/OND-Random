from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from jsonschema import Draft7Validator


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema: Dict[str, Any]) -> Draft7Validator:
    return Draft7Validator(schema)


def _report_errors(label: str, errors: Iterable[str]) -> int:
    count = 0
    for msg in errors:
        print(f"{label}: {msg}")
        count += 1
    return count


def _validate_json(label: str, obj: Any, validator: Draft7Validator) -> int:
    errors = []
    for err in validator.iter_errors(obj):
        path = ".".join(str(p) for p in err.path)
        loc = f" at {path}" if path else ""
        errors.append(f"{err.message}{loc}")
    return _report_errors(label, errors)


def _validate_observations(path: Path, validator: Draft7Validator) -> int:
    errors = 0
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                errors += _report_errors(str(path), [f"line {idx}: invalid json ({exc})"])
                continue
            for err in validator.iter_errors(obj):
                path_str = ".".join(str(p) for p in err.path)
                loc = f" at {path_str}" if path_str else ""
                errors += _report_errors(str(path), [f"line {idx}: {err.message}{loc}"])
                break
    return errors


def _detect_profile_schema(obj: Any, schemas: Dict[str, Draft7Validator]) -> Tuple[str, Draft7Validator] | None:
    if isinstance(obj, list):
        has_mean = any(isinstance(item, dict) and ("mean" in item or "std" in item) for item in obj)
        if has_mean:
            return "reference_profiles", schemas["reference_profiles"]
        return "ond_profiles", schemas["ond_profiles"]
    if isinstance(obj, dict):
        if all(k in obj for k in ("H_rank", "H_sub", "H_branch", "rank", "n_samples", "dimension")):
            return "ond_profile", schemas["ond_profile"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ODD/OND-ART artifacts against schemas.")
    parser.add_argument("--observations", action="append", default=[], help="Path to observations.jsonl")
    parser.add_argument("--ond-art-report", action="append", default=[], help="Path to ond_art_report.json")
    parser.add_argument("--profile", action="append", default=[], help="Path to OND profile JSON (single or list)")
    parser.add_argument("--reference-profiles", action="append", default=[], help="Path to reference_profiles.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    schemas_dir = root / "schemas"

    schema_observations = _load_json(schemas_dir / "observations_record.schema.json")
    schema_profile = _load_json(schemas_dir / "ond_profile.schema.json")
    schema_profiles = _load_json(schemas_dir / "ond_profiles.schema.json")
    schema_reference = _load_json(schemas_dir / "reference_profiles.schema.json")
    schema_report = _load_json(schemas_dir / "ond_art_report.schema.json")

    validators = {
        "observations": _validator(schema_observations),
        "ond_profile": _validator(schema_profile),
        "ond_profiles": _validator(schema_profiles),
        "reference_profiles": _validator(schema_reference),
        "ond_art_report": _validator(schema_report),
    }

    errors = 0

    for path_str in args.observations:
        path = Path(path_str)
        errors += _validate_observations(path, validators["observations"])

    for path_str in args.ond_art_report:
        path = Path(path_str)
        obj = _load_json(path)
        errors += _validate_json(str(path), obj, validators["ond_art_report"])

    for path_str in args.profile:
        path = Path(path_str)
        obj = _load_json(path)
        detected = _detect_profile_schema(obj, validators)
        if detected is None:
            errors += _report_errors(str(path), ["unrecognized profile structure"])
            continue
        _, validator = detected
        errors += _validate_json(str(path), obj, validator)

    for path_str in args.reference_profiles:
        path = Path(path_str)
        obj = _load_json(path)
        errors += _validate_json(str(path), obj, validators["reference_profiles"])

    if errors:
        print(f"Validation failed with {errors} error(s).")
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
