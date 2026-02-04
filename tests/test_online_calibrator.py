import numpy as np

from ond_random.ond import OnlineCalibrator


def test_online_calibrator_mean_std():
    cal = OnlineCalibrator(min_std=0.0)
    profiles = [
        {"H_rank": 1.0, "H_sub": 0.5, "H_branch": 0.2},
        {"H_rank": 0.0, "H_sub": 0.5, "H_branch": 0.4},
    ]
    cal.update_many(profiles)
    target = cal.target()
    assert np.isclose(target.mean["H_rank"], 0.5)
    assert np.isclose(target.mean["H_sub"], 0.5)
    assert np.isclose(target.mean["H_branch"], 0.3)
    assert np.isclose(target.std["H_rank"], np.sqrt(0.5))


def test_online_calibrator_state_roundtrip():
    cal = OnlineCalibrator()
    cal.update({"H_rank": 0.9, "H_sub": 0.8, "H_branch": 0.2})
    state = cal.state_dict()
    restored = OnlineCalibrator.from_state(state)
    assert restored.count == cal.count
    assert np.isclose(restored.mean["H_rank"], cal.mean["H_rank"])
