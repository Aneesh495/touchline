"""Squad continuity oracles."""

from touchline.economics.continuity import season_continuity


def test_minutes_weighted_rewards_keeping_the_core():
    # Previous season: a core player (3000 min) and a fringe player (300 min).
    prev = {"core": 3000.0, "fringe": 300.0}
    # Keep the core, drop the fringe, add a newcomer.
    current = {"core", "newcomer"}
    s = season_continuity(prev, current, "2022-2023", "2023-2024")
    # roster continuity is 1 of 2 = 0.5
    assert s.roster_continuity == 0.5
    # minutes-weighted continuity is 3000 / 3300, much higher than 0.5
    assert s.minutes_weighted_continuity > 0.9
    assert s.arrivals == 1
    assert s.departures == 1


def test_full_turnover_is_zero_continuity():
    prev = {"a": 1000.0, "b": 2000.0}
    current = {"c", "d"}
    s = season_continuity(prev, current, "x", "y")
    assert s.roster_continuity == 0.0
    assert s.minutes_weighted_continuity == 0.0
    assert s.departures == 2


def test_identical_squad_is_full_continuity():
    prev = {"a": 1000.0, "b": 2000.0}
    current = {"a", "b"}
    s = season_continuity(prev, current, "x", "y")
    assert s.roster_continuity == 1.0
    assert s.minutes_weighted_continuity == 1.0
    assert s.arrivals == 0
