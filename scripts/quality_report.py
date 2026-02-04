from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    report_path = Path("data/reports/benchmark_profiles.json")
    if not report_path.exists():
        raise SystemExit("benchmark_profiles.json not found; run benchmark first")

    profiles = json.loads(report_path.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in profiles}

    required_ids = ["I-ondmax", "Q-ideal", "Q-drift"]
    for rid in required_ids:
        if rid not in by_id:
            raise SystemExit(f"missing profile: {rid}")

    iid = by_id["I-ondmax"]
    qideal = by_id["Q-ideal"]
    qdrift = by_id["Q-drift"]

    checks = []

    # Sanity: H_rank ~ high for IID
    checks.append({
        "name": "H_rank close to 1 for IID",
        "pass": iid["H_rank"] > 0.95,
        "value": iid["H_rank"],
        "threshold": 0.95,
    })

    # Q-drift should have worse H_sub than IID
    checks.append({
        "name": "Q-drift H_sub lower than IID",
        "pass": qdrift["H_sub"] < iid["H_sub"],
        "iid": iid["H_sub"],
        "q_drift": qdrift["H_sub"],
    })

    # Q-drift should have lower H_branch than IID in delta mode
    checks.append({
        "name": "Q-drift H_branch lower than IID",
        "pass": qdrift["H_branch"] < iid["H_branch"],
        "iid": iid["H_branch"],
        "q_drift": qdrift["H_branch"],
    })

    # Q-ideal should be close to IID in H_sub
    checks.append({
        "name": "Q-ideal H_sub close to IID",
        "pass": abs(qideal["H_sub"] - iid["H_sub"]) < 0.02,
        "iid": iid["H_sub"],
        "q_ideal": qideal["H_sub"],
        "tolerance": 0.02,
    })

    passed = all(c["pass"] for c in checks)
    result = {
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
    }

    out_path = Path("data/reports/quality_report.json")
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    # Print summary
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
