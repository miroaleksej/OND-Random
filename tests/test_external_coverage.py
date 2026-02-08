import json
import subprocess
import sys
from pathlib import Path


def test_external_coverage_script_reports_missing(tmp_path):
    root = tmp_path / "external" / "large"
    (root / "practrand").mkdir(parents=True)
    (root / "nist" / "ondmax").mkdir(parents=True)
    (root / "testu01").mkdir(parents=True)
    (root / "practrand" / "ondmax_1gb.log").write_text("ok", encoding="utf-8")
    (root / "nist" / "ondmax" / "result.txt").write_text("ok", encoding="utf-8")
    (root / "testu01" / "ondmax_fips.txt").write_text("ok", encoding="utf-8")

    out = tmp_path / "coverage.json"
    cmd = [
        sys.executable,
        "scripts/check_external_coverage.py",
        "--root",
        str(root),
        "--rngs",
        "ondmax,system",
        "--out",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "incomplete"
    assert "system" in report["missing_targets"]
    assert report["coverage_ratio"] < 1.0


def test_external_coverage_script_strict_fails_when_missing(tmp_path):
    root = tmp_path / "external" / "large"
    root.mkdir(parents=True)
    cmd = [
        sys.executable,
        "scripts/check_external_coverage.py",
        "--root",
        str(root),
        "--rngs",
        "ondmax",
        "--strict",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 1


def test_external_coverage_reports_partial_quantum_with_fallback_artifacts(tmp_path):
    root = tmp_path / "external" / "large"
    (root / "practrand").mkdir(parents=True)
    (root / "nist" / "quantum_partial").mkdir(parents=True)
    (root / "testu01").mkdir(parents=True)

    # Quantum full large artifacts are intentionally absent.
    (root / "practrand" / "quantum_partial.log").write_text("length= 4 megabytes", encoding="utf-8")
    (root / "nist" / "quantum_partial" / "result.txt").write_text("STATISTICAL TEST", encoding="utf-8")
    (root / "testu01" / "quantum_partial_fips.txt").write_text(
        "Summary results of FIPS-140-2", encoding="utf-8"
    )

    out = tmp_path / "coverage_quantum_partial.json"
    cmd = [
        sys.executable,
        "scripts/check_external_coverage.py",
        "--root",
        str(root),
        "--rngs",
        "quantum",
        "--out",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "partial"
    assert report["missing_targets"] == []
    assert report["partial_targets"] == ["quantum"]
