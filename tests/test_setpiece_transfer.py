"""Set-piece conversion and transfer-adaptation oracles."""

from datetime import date

from touchline.models.set_pieces import SetPieceConversionModel, SetPieceOutcome
from touchline.models.transfer_adaptation import OutputPoint, summarise_adaptation


def test_setpiece_small_sample_shrinks():
    outcomes = [
        SetPieceOutcome("established", attempts=200, shots_within_horizon=60, goals_within_horizon=20, direct_goals=2),
        SetPieceOutcome("lucky", attempts=5, shots_within_horizon=3, goals_within_horizon=2, direct_goals=0),
    ]
    model = SetPieceConversionModel()
    ests = {e.key: e for e in model.fit_conversion(outcomes)}
    # lucky has the higher raw rate but shrinks far more than the established team
    assert ests["lucky"].raw_rate > ests["established"].raw_rate
    assert ests["lucky"].shrinkage_weight < ests["established"].shrinkage_weight


def test_direct_fraction_reported_not_divided_by_zero():
    none = [SetPieceOutcome("t", 10, 0, 0, 0)]
    assert SetPieceConversionModel.direct_fraction(none) == 0.0
    some = [SetPieceOutcome("t", 10, 4, 4, 1)]
    assert SetPieceConversionModel.direct_fraction(some) == 0.25


def test_transfer_adaptation_windows_are_chronologically_separated():
    move = date(2023, 1, 1)
    points = [
        OutputPoint(date(2022, 10, 1), per90=0.8, minutes=270),  # pre
        OutputPoint(date(2022, 12, 1), per90=0.7, minutes=180),  # pre
        OutputPoint(date(2023, 2, 1), per90=0.2, minutes=180),   # early post (dip)
        OutputPoint(date(2023, 9, 1), per90=0.6, minutes=270),   # late post (recovery)
    ]
    s = summarise_adaptation(points, move, early_days=120)
    assert s.pre_mean > s.post_early_mean  # a dip after the move
    assert s.recovery > 0  # recovery from early to late
    # pre exposure only counts pre-move minutes
    assert s.pre_exposure == 450.0


def test_match_on_move_date_counts_as_post():
    move = date(2023, 1, 1)
    points = [OutputPoint(date(2023, 1, 1), per90=0.5, minutes=90)]
    s = summarise_adaptation(points, move)
    assert s.pre_exposure == 0.0
    assert s.post_exposure == 90.0
