import json

import numpy as np

from ond_random.ond.observations_jsonl import ObservationsMeta, read_observations_jsonl, write_observations_jsonl


def test_observations_jsonl_roundtrip(tmp_path):
    U = np.array([[1, 2], [3, 4]], dtype=np.int64)
    meta = ObservationsMeta(
        pi_id="pi:test",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "R^d", "d": 2},
    )
    out = tmp_path / "obs.jsonl"
    write_observations_jsonl(str(out), U, meta)
    meta2, U2, invalid = read_observations_jsonl(str(out))
    assert invalid == 0
    assert meta2["pi_id"] == "pi:test"
    assert U2.shape == (2, 2)
    assert np.all(U2 == U)


def test_observations_jsonl_large_ints(tmp_path):
    big = 2**80 + 3
    U = np.array([[big, big + 1]], dtype=object)
    meta = ObservationsMeta(
        pi_id="pi:big",
        pi_version="1.0.0",
        pi_spec_hash="sha256:deadbeef",
        obs_space={"type": "Z_mod_m", "modulus": big + 5, "d": 2},
    )
    out = tmp_path / "obs.jsonl"
    write_observations_jsonl(str(out), U, meta, stringify_large_ints=True)
    raw = out.read_text(encoding="utf-8").splitlines()
    obs_line = json.loads(raw[1])
    assert isinstance(obs_line["u"][0], str)
    meta2, U2, invalid = read_observations_jsonl(str(out))
    assert invalid == 0
    assert int(U2[0, 0]) == big

