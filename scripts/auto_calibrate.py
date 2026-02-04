from __future__ import annotations

import argparse
import json
from pathlib import Path

from ond_random.ond import OnlineCalibrator
from ond_random.ond.benchmark import ReferenceProfile, load_reference_profiles, save_reference_profiles, ONDClass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="data/reports/benchmark_profiles.json")
    parser.add_argument("--out", default="data/reports/auto_calibration.json")
    parser.add_argument("--ond-class", choices=[c.value for c in ONDClass], help="filter profiles by class")
    parser.add_argument("--update-references", action="store_true")
    parser.add_argument("--reference-path", default="data/benchmarks/reference_profiles.json")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(f"report not found: {report_path}")

    profiles = json.loads(report_path.read_text(encoding="utf-8"))
    if args.ond_class:
        profiles = [p for p in profiles if p.get("ond_class") == args.ond_class]
        if not profiles:
            raise SystemExit(f"no profiles for class {args.ond_class}")

    calibrator = OnlineCalibrator()
    calibrator.update_many(profiles)
    target = calibrator.target(description="online")

    key = f"class:{args.ond_class}" if args.ond_class else "all"
    out = {
        "updated_key": key,
        "targets": {
            key: {
                "count": calibrator.count,
                "mean": target.mean,
                "std": target.std,
                "description": target.description,
            }
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))

    if args.update_references:
        if not args.ond_class:
            raise SystemExit("--update-references requires --ond-class")
        ref_path = Path(args.reference_path)
        refs = []
        if ref_path.exists():
            refs = load_reference_profiles(str(ref_path))
        cls = ONDClass(args.ond_class)
        updated = False
        for ref in refs:
            if ref.ond_class == cls:
                ref.mean = dict(target.mean)
                ref.std = dict(target.std)
                ref.description = "online-calibrated"
                updated = True
        if not updated:
            refs.append(ReferenceProfile(ond_class=cls, mean=dict(target.mean), std=dict(target.std), description="online-calibrated"))
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        save_reference_profiles(str(ref_path), refs)


if __name__ == "__main__":
    main()
