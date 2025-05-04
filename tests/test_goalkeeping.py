"""Goalkeeping eligibility oracles."""

from touchline.models.goalkeeping import (
    ShotFaced,
    goalkeeping_report,
    save_percentage,
)


def test_goals_prevented_unavailable_without_placement():
    shots = [
        ShotFaced(on_target=True, goal=False, placement_known=True, post_shot_xg=0.3),
        ShotFaced(on_target=True, goal=True, placement_known=False, post_shot_xg=None),
    ]
    r = goalkeeping_report(shots)
    assert r.goals_prevented is None
    assert not r.eligible
    assert "placement" in r.reason


def test_goals_prevented_computed_with_placement():
    shots = [
        ShotFaced(True, False, True, 0.3),
        ShotFaced(True, False, True, 0.6),  # a save of a high-xG shot
        ShotFaced(True, True, True, 0.2),   # conceded a low-xG shot
    ]
    r = goalkeeping_report(shots)
    assert r.eligible
    # expected conceded 0.3+0.6+0.2 = 1.1; actual 1 -> prevented 0.1
    assert abs(r.goals_prevented - 0.1) < 1e-9


def test_save_percentage_always_available():
    shots = [
        ShotFaced(True, False, False, None),
        ShotFaced(True, True, False, None),
        ShotFaced(False, False, False, None),  # off target, ignored
    ]
    assert abs(save_percentage(shots) - 0.5) < 1e-9
