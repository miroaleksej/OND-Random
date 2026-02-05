import json

from ond_random.ond.baseline_policy import load_policy, select_policy


def test_baseline_policy_default(tmp_path):
    policy = {
        "version": "0.1",
        "default": {"percentiles": [50, 80, 95], "profile": "core"},
        "domains": [],
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    data = load_policy(str(path))
    pct, profile = select_policy(data, protocol="custom", scheme="custom")
    assert pct == (50.0, 80.0, 95.0)
    assert profile == "core"


def test_baseline_policy_match(tmp_path):
    policy = {
        "version": "0.1",
        "default": {"percentiles": [50, 80, 95], "profile": "core"},
        "domains": [
            {"protocol": "physics", "scheme": "LHC-*", "percentiles": [40, 70, 90], "profile": "dev"}
        ],
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    data = load_policy(str(path))
    pct, profile = select_policy(data, protocol="physics", scheme="LHC-v1")
    assert pct == (40.0, 70.0, 90.0)
    assert profile == "dev"

