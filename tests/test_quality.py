"""Data-quality reconciliation oracles."""

from touchline.quality.reconcile import (
    check_lineup_completeness,
    check_red_card_manpower,
    reconcile_score,
)


def test_clean_score_reconciles():
    r = reconcile_score("m1", 2, 1, 2, 1)
    assert r.is_clean


def test_own_goal_accounted_for():
    # Home wins 2-1; one home goal was an own goal by an away player (event is on
    # the away side but the recorded goal is for home).
    r = reconcile_score(
        "m2",
        goal_events_home=1,
        goal_events_away=1,
        recorded_home=2,
        recorded_away=1,
        own_goals_for_home=1,
    )
    assert r.is_clean


def test_score_mismatch_reported_not_fixed():
    r = reconcile_score("m3", 1, 1, 3, 1)
    assert not r.is_clean
    assert any("home" in d for d in r.discrepancies)


def test_lineup_gap_detected():
    r = check_lineup_completeness("m4", home_starters=10, away_starters=11)
    assert not r.is_clean
    assert "home" in r.discrepancies[0]


def test_red_card_manpower_mismatch():
    r = check_red_card_manpower("m5", red_cards=1, manpower_reductions=0)
    assert not r.is_clean


def test_red_card_manpower_consistent():
    r = check_red_card_manpower("m6", red_cards=2, manpower_reductions=2)
    assert r.is_clean
