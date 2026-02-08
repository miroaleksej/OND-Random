import json
from pathlib import Path

from ond_random.cli import build_parser


def test_run_suite_ond_only(tmp_path: Path) -> None:
    out_dir = tmp_path / "run_suite"
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-suite",
            "--suite",
            "ond",
            "--out",
            str(out_dir),
            "--ond-samples",
            "200",
            "--ond-dimension",
            "2",
            "--ond-word-bits",
            "16",
        ]
    )
    args.func(args)
    results_path = out_dir / "results.json"
    metadata_path = out_dir / "metadata.json"
    assert results_path.exists()
    assert metadata_path.exists()
    results = json.loads(results_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert results["suites"]["ond"]["status"] == "ok"
    assert (out_dir / "artifacts" / "ond" / "observations.jsonl").exists()
    assert isinstance(metadata.get("git"), dict)
    assert isinstance(metadata["git"].get("commit"), str)
    assert len(metadata["git"]["commit"]) > 0
