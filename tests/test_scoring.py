from ond_random.ond.scoring import score_profile, ONDTarget


def test_score_profile_monotonic():
    target = ONDTarget(mean={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}, std={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0})
    good = {"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}
    bad = {"H_rank": 0.5, "H_sub": 0.5, "H_branch": 0.5}
    score_good = score_profile(good, target=target)
    score_bad = score_profile(bad, target=target)
    assert score_good.score > score_bad.score
