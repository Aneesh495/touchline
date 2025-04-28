"""Counterfactual, comparison, and schedule oracles."""

from dataclasses import replace

from touchline.analysis.compare import PlayerStat, compare_players
from touchline.analysis.counterfactual import (
    CounterfactualScenario,
    apply_scenario,
)
from touchline.features.schedule import strength_of_schedule
from touchline.features.shots import ShotFeatureRow
from touchline.features.team_strength import MatchRow


def _row(dist, angle):
    return ShotFeatureRow(
        distance_m=dist, angle_rad=angle, is_header=0, is_penalty=0,
        is_free_kick=0, is_corner=0, is_counter=0, has_spatial=0,
        defenders_in_cone=None, gk_distance_m=None, is_goal=0,
    )


def test_counterfactual_is_labelled_model_scenario():
    row = _row(20.0, 0.3)

    # a simple linear "model": closer shots score more
    def predict(v):
        return max(0.0, min(1.0, 0.9 - 0.03 * v[0]))

    scenario = CounterfactualScenario(
        "move the shot 10 m closer",
        lambda r: replace(r, distance_m=r.distance_m - 10.0),
    )
    res = apply_scenario(row, scenario, predict)
    assert res.is_model_scenario
    assert res.scenario_xg > res.baseline_xg  # closer -> higher
    assert "model scenario" in res.caption()
    assert "not an observed outcome" in res.caption()


def test_comparison_filters_and_flags_small_samples():
    stats = [
        PlayerStat("established", "FW", value=0.6, minutes=2700, goals_like_count=18),
        PlayerStat("cameo", "FW", value=2.0, minutes=90, goals_like_count=2),
        PlayerStat("defender", "DF", value=0.1, minutes=2700, goals_like_count=3),
    ]
    rows = compare_players(stats, min_minutes=450, role_filter="FW")
    assert [r.player for r in rows][0] == "cameo"  # highest raw value
    cameo = next(r for r in rows if r.player == "cameo")
    assert cameo.limited_sample  # flagged despite topping the list
    # the cameo's interval is very wide (few goals)
    assert cameo.ci_high - cameo.ci_low > rows[-1].ci_high - rows[-1].ci_low
    # role filter excluded the defender
    assert all(r.role == "FW" for r in rows)


def test_strength_of_schedule_over_performance():
    strength = {"weak": -0.5, "strong": 0.5}
    matches = [
        MatchRow("me", "weak", 3, 0, __import__("datetime").date(2022, 8, 1), "LG", "2022-2023"),
        MatchRow("strong", "me", 1, 1, __import__("datetime").date(2022, 8, 8), "LG", "2022-2023"),
    ]

    # average team expected points: more for easier opponents
    def avg_wp(diff):
        return 1.5 + diff  # toy monotone function

    s = strength_of_schedule(matches, "me", strength, avg_wp)
    assert s.matches == 2
    assert s.points == 4  # a win (3) and a draw (1)
    # over_performance is actual minus expected
    assert isinstance(s.over_performance, float)
