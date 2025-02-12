"""UCL era-specific rules and coverage matrix oracles."""

import pytest

from touchline.coverage.matrix import CoverageMatrix, FieldLevel
from touchline.simulate.ucl import (
    LeaguePhaseQualification,
    LegResult,
    away_goals_in_force,
    decide_two_legged_tie,
    group_stage_qualifies,
    uses_league_phase,
)


def test_away_goals_era_boundary():
    assert away_goals_in_force(2019) is True
    assert away_goals_in_force(2020) is True
    assert away_goals_in_force(2021) is False  # abolished from 2021-22


def test_league_phase_era_boundary():
    assert uses_league_phase(2023) is False
    assert uses_league_phase(2024) is True


def test_away_goals_decides_level_tie_in_old_era():
    # Aggregate 2-2. Team A scored 1 away (leg2), team B scored 2 away (leg1).
    leg1 = LegResult("A", "B", 0, 2)  # at A: A 0, B 2
    leg2 = LegResult("B", "A", 0, 1)  # at B: B 0, A 1 -> wait recompute below
    # aggregate A = leg1.home(0) + leg2.away(1) = 1; B = leg1.away(2)+leg2.home(0)=2
    # that is not level; adjust to make it level:
    leg1 = LegResult("A", "B", 1, 2)
    leg2 = LegResult("B", "A", 1, 2)
    # A = 1 + 2 = 3 ; B = 2 + 1 = 3 -> level. A away = leg2.away = 2; B away = leg1.away = 2
    # still equal away; make A away higher:
    leg2 = LegResult("B", "A", 0, 1)
    # A = leg1.home(1) + leg2.away(1) = 2; B = leg1.away(2) + leg2.home(0) = 2 level
    # A away = leg2.away = 1; B away = leg1.away = 2 -> B advances on away goals
    out = decide_two_legged_tie("A", "B", leg1, leg2, season_start_year=2019)
    assert out.reason == "away_goals"
    assert out.winner == "B"


def test_no_away_goals_after_abolition_goes_to_extra_time_or_pens():
    leg1 = LegResult("A", "B", 1, 0)
    leg2 = LegResult("B", "A", 1, 0)
    # aggregate level 1-1; no away goals in 2022; needs ET then penalties
    out = decide_two_legged_tie(
        "A", "B", leg1, leg2, season_start_year=2022, extra_time_goals=(0, 0),
        shootout=(4, 2),
    )
    assert out.reason == "penalties"
    assert out.winner == "A"


def test_extra_time_decides_before_penalties():
    leg1 = LegResult("A", "B", 1, 1)
    leg2 = LegResult("B", "A", 1, 1)
    # level 2-2; ET: A scores once
    out = decide_two_legged_tie(
        "A", "B", leg1, leg2, season_start_year=2022, extra_time_goals=(1, 0)
    )
    assert out.reason == "extra_time"
    assert out.winner == "A"


def test_level_after_et_without_shootout_raises():
    leg1 = LegResult("A", "B", 0, 0)
    leg2 = LegResult("B", "A", 0, 0)
    with pytest.raises(ValueError):
        decide_two_legged_tie("A", "B", leg1, leg2, 2022)


def test_league_phase_qualification_mapping():
    assert LeaguePhaseQualification(3).outcome() == "round_of_16_direct"
    assert LeaguePhaseQualification(12).outcome() == "knockout_playoff"
    assert LeaguePhaseQualification(30).outcome() == "eliminated"
    assert group_stage_qualifies(2) is True
    assert group_stage_qualifies(3) is False


def test_coverage_distinguishes_field_depth():
    m = CoverageMatrix()
    m.add_match("EPL", "2021-2022", "m1")  # results only
    m.add_match("EPL", "2021-2022", "m2", has_events=True)
    m.add_match("LALIGA", "2021-2022", "m3", has_events=True, has_tracking=True)
    assert m.cell("EPL", "2021-2022").field_level is FieldLevel.EVENTS
    assert m.cell("LALIGA", "2021-2022").field_level is FieldLevel.TRACKING
    assert m.total_matches() == 3
    assert m.total_event_matches() == 2


def test_coverage_unique_counts_not_inflated_by_duplicates():
    m = CoverageMatrix()
    m.add_match("EPL", "2021-2022", "m1")
    m.add_match("EPL", "2021-2022", "m1")  # same id from another feed
    assert m.total_matches() == 1


def test_coverage_profile_check_reports_shortfall():
    m = CoverageMatrix()
    m.add_match("EPL", "2021-2022", "m1")
    ok, reasons = m.meets_profile(
        min_matches=100, min_event_matches=50, required_competitions={"EPL", "UCL"}
    )
    assert ok is False
    assert any("matches" in r for r in reasons)
    assert any("UCL" in r for r in reasons)
