"""Free-kick and corner classification oracles."""

from touchline.domain.geometry import Point
from touchline.models.free_kicks import (
    CornerDelivery,
    FreeKickCounts,
    FreeKickType,
    classify_corner,
    classify_free_kick,
)


def test_direct_shot_free_kick():
    t = classify_free_kick(Point(0.8, 0.5), None, took_shot=True)
    assert t is FreeKickType.DIRECT_SHOT


def test_cross_free_kick():
    t = classify_free_kick(Point(0.6, 0.1), Point(0.9, 0.5), took_shot=False)
    assert t is FreeKickType.CROSS


def test_free_kick_unknown_without_end():
    t = classify_free_kick(Point(0.6, 0.1), None, took_shot=False)
    assert t is FreeKickType.UNKNOWN


def test_corner_unknown_without_trajectory():
    d = classify_corner(from_left=True, end=Point(0.88, 0.5), trajectory_known=False)
    assert d is CornerDelivery.UNKNOWN


def test_corner_inswinger_with_trajectory():
    d = classify_corner(from_left=True, end=Point(0.95, 0.5), trajectory_known=True)
    assert d is CornerDelivery.INSWINGER


def test_short_corner_detected():
    d = classify_corner(from_left=True, end=Point(0.85, 0.05), trajectory_known=True)
    assert d is CornerDelivery.SHORT


def test_free_kick_foul_discrepancy_is_advantage():
    c = FreeKickCounts(fouls=12, free_kicks_recorded=10)
    assert c.discrepancy() == 2  # two fouls had advantage played, no FK recorded
