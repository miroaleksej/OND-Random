import json

import numpy as np

from ond_random.ond.observations_jsonl import ObservationsMeta, write_observations_jsonl
from ond_random.ond.odd_report import build_ond_art_report


def test_odd_report_with_baseline(tmp_path):
    U = np.random.default_rng(0).normal(size=(200, 3))
    meta = ObservationsMeta(
        pi_id="pi:test",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "R^d", "d": 3},
    )
    base_path = tmp_path / "baseline.jsonl"
    write_observations_jsonl(str(base_path), U, meta)
    obs_path = tmp_path / "obs.jsonl"
    write_observations_jsonl(str(obs_path), U, meta)

    report = build_ond_art_report(
        observations_path=str(obs_path),
        baseline_observations=str(base_path),
        baseline_id="base-1",
        bins=8,
        bootstrap_samples=50,
        bootstrap_seed=1,
    )
    assert report["baseline"] is not None
    assert report["baseline"]["classification"] in {
        "Within Baseline Envelope",
        "Deviating",
        "Strong Deviation",
    }
    assert report["data"]["N"] == 200
    assert report["pi"]["pi_id"] == "pi:test"


def test_odd_report_serializable(tmp_path):
    U = np.random.default_rng(1).normal(size=(50, 2))
    meta = ObservationsMeta(
        pi_id="pi:test",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "R^d", "d": 2},
    )
    obs_path = tmp_path / "obs.jsonl"
    write_observations_jsonl(str(obs_path), U, meta)
    report = build_ond_art_report(observations_path=str(obs_path), bins=6, bootstrap_samples=20)
    payload = json.dumps(report)
    assert "OND-ART" in payload
    assert ("baseline" not in report) or isinstance(report["baseline"], dict)
