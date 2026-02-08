from __future__ import annotations

import argparse
import json
import sys
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from jsonschema import Draft7Validator

from .compat import compatibility_notes


SCHEMA_FILES = {
    "observations_record": "observations_record.schema.json",
    "ond_art_report": "ond_art_report.schema.json",
    "ond_profile": "ond_profile.schema.json",
    "ond_profiles": "ond_profiles.schema.json",
    "reference_profiles": "reference_profiles.schema.json",
}


def _load_schema(name: str) -> Dict[str, Any]:
    filename = SCHEMA_FILES[name]
    text = resources.files("ond_odd_spec.schemas").joinpath(filename).read_text(encoding="utf-8")
    return json.loads(text)


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


def validate_artifacts(
    *,
    observations: List[str],
    ond_art_reports: List[str],
    profiles: List[str],
    reference_profiles: List[str],
    allow_older_majors: bool = False,
) -> int:
    schema_observations = _load_schema("observations_record")
    schema_report = _load_schema("ond_art_report")
    schema_profile = _load_schema("ond_profile")
    schema_profiles = _load_schema("ond_profiles")
    schema_reference = _load_schema("reference_profiles")

    validators = {
        "observations": _validator(schema_observations),
        "ond_art_report": _validator(schema_report),
        "ond_profile": _validator(schema_profile),
        "ond_profiles": _validator(schema_profiles),
        "reference_profiles": _validator(schema_reference),
    }

    errors = 0

    for path_str in observations:
        path = Path(path_str)
        errors += _validate_observations(path, validators["observations"])
        if not allow_older_majors:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(obj, dict) and (obj.get("type") == "meta" or ("pi_id" in obj and "pi_version" in obj)):
                        notes = compatibility_notes(obj.get("spec"))
                        if notes:
                            errors += _report_errors(str(path), notes)
                        break

    for path_str in ond_art_reports:
        path = Path(path_str)
        obj = json.loads(path.read_text(encoding="utf-8"))
        errors += _validate_json(str(path), obj, validators["ond_art_report"])
        if isinstance(obj, dict) and not allow_older_majors:
            notes = compatibility_notes(obj.get("spec"))
            if notes:
                errors += _report_errors(str(path), notes)

    for path_str in profiles:
        path = Path(path_str)
        obj = json.loads(path.read_text(encoding="utf-8"))
        detected = _detect_profile_schema(obj, validators)
        if detected is None:
            errors += _report_errors(str(path), ["unrecognized profile structure"])
            continue
        _, validator = detected
        errors += _validate_json(str(path), obj, validator)

    for path_str in reference_profiles:
        path = Path(path_str)
        obj = json.loads(path.read_text(encoding="utf-8"))
        errors += _validate_json(str(path), obj, validators["reference_profiles"])

    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ODD/OND-ART artifacts against schemas.")
    parser.add_argument("--observations", action="append", default=[], help="Path to observations.jsonl")
    parser.add_argument("--ond-art-report", action="append", default=[], help="Path to ond_art_report.json")
    parser.add_argument("--profile", action="append", default=[], help="Path to OND profile JSON (single or list)")
    parser.add_argument("--reference-profiles", action="append", default=[], help="Path to reference_profiles.json")
    parser.add_argument(
        "--allow-older-majors",
        action="store_true",
        help="Allow older spec/schema major versions (compat mode)",
    )
    args = parser.parse_args(argv)

    errors = validate_artifacts(
        observations=args.observations,
        ond_art_reports=args.ond_art_report,
        profiles=args.profile,
        reference_profiles=args.reference_profiles,
        allow_older_majors=args.allow_older_majors,
    )

    if errors:
        print(f"Validation failed with {errors} error(s).")
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
