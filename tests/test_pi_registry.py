import json

from ond_random.ond.pi_registry import add_entry, check_entry, load_registry, save_registry


def test_registry_add_and_check(tmp_path):
    path = tmp_path / "registry.json"
    reg = load_registry(str(path))
    add_entry(
        reg,
        pi_id="pi:test",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "R^d", "d": 2},
    )
    save_registry(str(path), reg)
    reg2 = json.loads(path.read_text(encoding="utf-8"))
    check_entry(reg2, pi_id="pi:test", pi_version="1.0.0", pi_spec_hash="sha256:deadbeef")


def test_registry_drift_raises(tmp_path):
    path = tmp_path / "registry.json"
    reg = load_registry(str(path))
    add_entry(
        reg,
        pi_id="pi:test",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "R^d", "d": 2},
    )
    save_registry(str(path), reg)
    reg2 = load_registry(str(path))
    try:
        check_entry(reg2, pi_id="pi:test", pi_version="1.0.0", pi_spec_hash="sha256:badcafe")
        assert False, "expected drift error"
    except ValueError:
        pass
