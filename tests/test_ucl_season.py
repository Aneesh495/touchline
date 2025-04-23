"""Full UCL season (league phase + knockout) oracles."""

import math

import pytest

from touchline.simulate.ucl_season import (
    league_phase_cutoffs,
    simulate_ucl_season,
)


def _standings(n=36):
    return [f"T{i:02d}" for i in range(1, n + 1)]


def test_league_phase_cutoffs_bands():
    direct, playoff, out = league_phase_cutoffs(_standings())
    assert len(direct) == 8  # positions 1-8
    assert len(playoff) == 16  # positions 9-24
    assert len(out) == 12  # positions 25-36


def test_pre_2024_format_rejected_on_this_path():
    with pytest.raises(ValueError):
        simulate_ucl_season(_standings(), lambda a, b: 0.5, season_start_year=2022)


def test_direct_qualifiers_win_more_than_playoff_teams():
    standings = _standings()

    # Strength decreases with position; a higher-seeded team usually wins.
    def wp(a, b):
        ra = -int(a[1:])
        rb = -int(b[1:])
        return 1.0 / (1.0 + math.pow(10.0, -(ra - rb) / 5.0))

    res = simulate_ucl_season(standings, wp, season_start_year=2024, n_sims=1500, seed=1)
    # The top seed should have a higher title probability than a mid play-off team.
    assert res.title_prob("T01") > res.title_prob("T20")
    # title counts sum to at most n_sims (some sims may skip if degenerate)
    assert sum(res.title_counts.values()) <= res.n_sims
