"""Chronological split, group integrity, and Elo feature oracles."""

from datetime import date

from touchline.features.splits import (
    DatedItem,
    chronological_split,
    competition_holdout_split,
    rolling_origin_splits,
)
from touchline.features.team_strength import MatchRow, build_elo_features


def _items():
    return [
        DatedItem("a", date(2021, 8, 1), "EPL|2021-2022", "EPL"),
        DatedItem("b", date(2022, 1, 1), "EPL|2021-2022", "EPL"),
        DatedItem("c", date(2022, 8, 1), "EPL|2022-2023", "EPL"),
        DatedItem("d", date(2023, 1, 1), "EPL|2022-2023", "EPL"),
    ]


def test_chronological_split_respects_cut():
    items = _items()
    s = chronological_split(items, cut=date(2022, 7, 1))
    assert s.train == ["a", "b"]
    assert s.test == ["c", "d"]


def test_chronological_split_group_integrity():
    items = _items()
    # Cut mid-season would split a group across train/test: detect it.
    bad = chronological_split(items, cut=date(2021, 12, 1))
    assert bad.group_integrity_ok(items) is False
    # A season-boundary cut keeps groups intact.
    good = chronological_split(items, cut=date(2022, 7, 1))
    assert good.group_integrity_ok(items) is True


def test_competition_holdout():
    items = [
        DatedItem("a", date(2021, 8, 1), "EPL|2021-2022", "EPL"),
        DatedItem("u", date(2021, 9, 1), "UCL|2021-2022", "UCL"),
    ]
    s = competition_holdout_split(items, held_out="UCL")
    assert s.train == ["a"]
    assert s.test == ["u"]
    assert s.held_out_competition == "UCL"


def test_rolling_origin_windows():
    items = _items()
    cuts = [date(2022, 7, 1), date(2023, 7, 1)]
    splits = rolling_origin_splits(items, cuts)
    assert len(splits) == 2
    # First fold: train on 2021-22, test on 2022-23 window.
    assert splits[0].train == ["a", "b"]
    assert splits[0].test == ["c", "d"]
    # Second fold: train on everything before 2023-07, test on the rest (none).
    assert splits[1].train == ["a", "b", "c", "d"]
    assert splits[1].test == []


def test_elo_features_are_pre_match_only():
    matches = [
        MatchRow("A", "B", 3, 0, date(2021, 8, 1), "EPL", "2021-2022"),
        MatchRow("A", "B", 2, 0, date(2021, 8, 8), "EPL", "2021-2022"),
    ]
    rows = build_elo_features(matches)
    # First meeting: both start at base rating, so diff is zero.
    assert rows[0].elo_diff == 0.0
    # Second meeting: A has won once, so A's pre-match rating now exceeds B's.
    assert rows[1].home_elo_pre > rows[1].away_elo_pre
    # Probabilities are valid and ordered toward the stronger side.
    assert abs(rows[1].home_prob + rows[1].draw_prob + rows[1].away_prob - 1.0) < 1e-9
    assert rows[1].home_prob > rows[1].away_prob


def test_elo_features_sorted_by_date():
    matches = [
        MatchRow("A", "B", 1, 0, date(2022, 1, 1), "EPL", "2021-2022"),
        MatchRow("A", "B", 0, 1, date(2021, 8, 1), "EPL", "2021-2022"),
    ]
    rows = build_elo_features(matches)
    assert rows[0].when < rows[1].when
