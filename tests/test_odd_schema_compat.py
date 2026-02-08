import json
from pathlib import Path

from jsonschema import Draft7Validator


def test_ond_art_schema_accepts_legacy_null_baseline() -> None:
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schemas" / "ond_art_report.schema.json"
    report_path = root / "data" / "reports" / "cases" / "low_bits_bias" / "ond_art_report.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["baseline"] = None

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(report))
    assert not errors
