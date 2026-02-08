from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Tuple

from .provenance import resolve_provenance


@dataclass
class MigrationStats:
    files: int = 0
    updated: int = 0
    meta_updated: int = 0
    spec_added: int = 0
    spec_version_added: int = 0
    schema_version_added: int = 0


def _ensure_spec_fields(
    spec: Any,
    *,
    name: str,
    version: str,
    spec_version: str,
    schema_version: str,
) -> Tuple[dict, bool, MigrationStats]:
    stats = MigrationStats()
    changed = False
    if not isinstance(spec, dict):
        spec = {}
        changed = True
        stats.spec_added += 1
    if "name" not in spec:
        spec["name"] = name
        changed = True
    if "version" not in spec:
        spec["version"] = version
        changed = True
    if "spec_version" not in spec:
        spec["spec_version"] = spec_version
        changed = True
        stats.spec_version_added += 1
    if "schema_version" not in spec:
        spec["schema_version"] = schema_version
        changed = True
        stats.schema_version_added += 1
    return spec, changed, stats


def _write_atomic(path: Path, lines: Iterable[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line)
    os.replace(tmp, path)


def migrate_observations_jsonl(
    input_path: str,
    output_path: str,
    *,
    spec_version: str = "0.2",
    schema_version: str = "0.2",
) -> MigrationStats:
    stats = MigrationStats(files=1)
    in_path = Path(input_path)
    out_path = Path(output_path)
    lines_out = []
    meta_updated = False

    with in_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.rstrip("\n")
            if not raw:
                lines_out.append(line)
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                lines_out.append(line)
                continue
            if isinstance(obj, dict) and (obj.get("type") == "meta" or ("pi_id" in obj and "pi_version" in obj)):
                spec, changed, spec_stats = _ensure_spec_fields(
                    obj.get("spec"),
                    name="ODD-OBS",
                    version="0.1",
                    spec_version=spec_version,
                    schema_version=schema_version,
                )
                if spec.get("spec_version") != spec_version:
                    spec["spec_version"] = spec_version
                    changed = True
                if spec.get("schema_version") != schema_version:
                    spec["schema_version"] = schema_version
                    changed = True

                provenance = obj.get("provenance")
                if not isinstance(provenance, dict):
                    generator_id = obj.get("pi_id") or "unknown"
                    obj["provenance"] = resolve_provenance(
                        generator_id=str(generator_id),
                        profile_id="observations",
                        commit="unknown",
                        platform="unknown",
                    )
                    changed = True
                if changed:
                    obj["spec"] = spec
                    meta_updated = True
                    stats.meta_updated += 1
                    stats.spec_added += spec_stats.spec_added
                    stats.spec_version_added += spec_stats.spec_version_added
                    stats.schema_version_added += spec_stats.schema_version_added
                lines_out.append(json.dumps(obj, ensure_ascii=False) + "\n")
            else:
                lines_out.append(line)

    if meta_updated:
        stats.updated += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_path, lines_out)
    return stats


def migrate_ond_art_report(
    input_path: str,
    output_path: str,
    *,
    spec_version: str = "0.2",
    schema_version: str = "0.2",
) -> MigrationStats:
    stats = MigrationStats(files=1)
    in_path = Path(input_path)
    out_path = Path(output_path)
    obj = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return stats

    spec, changed, spec_stats = _ensure_spec_fields(
        obj.get("spec"),
        name="OND-ART",
        version="0.1",
        spec_version=spec_version,
        schema_version=schema_version,
    )
    if spec.get("spec_version") != spec_version:
        spec["spec_version"] = spec_version
        changed = True
    if spec.get("schema_version") != schema_version:
        spec["schema_version"] = schema_version
        changed = True

    if changed:
        obj["spec"] = spec
        stats.updated += 1
        stats.spec_added += spec_stats.spec_added
        stats.spec_version_added += spec_stats.spec_version_added
        stats.schema_version_added += spec_stats.schema_version_added

    if "provenance" not in obj or not isinstance(obj.get("provenance"), dict):
        pi = obj.get("pi") if isinstance(obj.get("pi"), dict) else {}
        generator_id = pi.get("pi_id") if isinstance(pi, dict) else None
        profile_id = spec.get("profile") if isinstance(spec, dict) else None
        obj["provenance"] = resolve_provenance(
            generator_id=str(generator_id) if generator_id else "unknown",
            profile_id=str(profile_id) if profile_id else "unknown",
            commit="unknown",
            platform="unknown",
        )
        stats.updated += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return stats
