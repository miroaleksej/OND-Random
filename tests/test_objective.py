from ond_random.ond.objective import auto_weights_from_profiles, objective_from_profiles
from ond_random.ond.scoring import ONDTarget


def test_auto_weights():
    profiles = {
        "a": {"H_rank": 1.0, "H_sub": 0.9, "H_branch": 0.8},
        "b": {"H_rank": 1.0, "H_sub": 0.91, "H_branch": 0.79},
    }
    w = auto_weights_from_profiles(profiles)
    assert w["H_rank"] >= w["H_sub"]


def test_objective_scores():
    target = ONDTarget(mean={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}, std={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0})
    profiles = {
        "a": {"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0},
        "b": {"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0},
    }
    result = objective_from_profiles(profiles, target=target)
    assert result.score > 50
