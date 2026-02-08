from __future__ import annotations

import argparse
from pathlib import Path

from ond_random.ond.migrate import migrate_observations_jsonl, migrate_ond_art_report


def _resolve_output_path(input_path: Path, out_dir: Path | None, in_place: bool) -> Path:
    if in_place:
        return input_path
    if out_dir is None:
        raise SystemExit("Use --out-dir or --in-place")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / input_path.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate ODD/OND-ART artifacts to current spec/schema version.")
    parser.add_argument("--observations", action="append", default=[], help="Path to observations.jsonl")
    parser.add_argument("--ond-art-report", action="append", default=[], help="Path to ond_art_report.json")
    parser.add_argument("--spec-version", default="0.2", help="Target spec_version")
    parser.add_argument("--schema-version", default="0.2", help="Target schema_version")
    parser.add_argument("--out-dir", help="Output directory (required unless --in-place)")
    parser.add_argument("--in-place", action="store_true", help="Update files in-place")
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    total_updates = 0
    total_files = 0

    for path_str in args.observations:
        in_path = Path(path_str)
        out_path = _resolve_output_path(in_path, out_dir, args.in_place)
        stats = migrate_observations_jsonl(
            str(in_path),
            str(out_path),
            spec_version=args.spec_version,
            schema_version=args.schema_version,
        )
        total_updates += stats.updated
        total_files += stats.files

    for path_str in args.ond_art_report:
        in_path = Path(path_str)
        out_path = _resolve_output_path(in_path, out_dir, args.in_place)
        stats = migrate_ond_art_report(
            str(in_path),
            str(out_path),
            spec_version=args.spec_version,
            schema_version=args.schema_version,
        )
        total_updates += stats.updated
        total_files += stats.files

    print(f"Migrated {total_updates}/{total_files} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
