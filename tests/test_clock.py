"""Clock correctness oracles.

These expected outcomes are reasoned by hand here, independent of the
implementation, so they genuinely test it rather than restate it.
"""

import pytest

from touchline.domain.clock import MatchClock, PeriodKind


def test_added_time_distinct_from_later_minute():
    # 45:00 + 2:00 of the first half must not equal 47:00 of some period.
    stoppage = MatchClock(PeriodKind.FIRST_HALF, second=45 * 60, added=2 * 60)
    assert stoppage.display() == "45+2"
    # A second-half event at minute 46 is clearly later than first-half stoppage.
    second_half = MatchClock(PeriodKind.SECOND_HALF, second=46)
    assert stoppage < second_half


def test_ordering_across_periods():
    order = [
        MatchClock(PeriodKind.FIRST_HALF, 10 * 60),
        MatchClock(PeriodKind.SECOND_HALF, 1),
        MatchClock(PeriodKind.EXTRA_FIRST, 1),
        MatchClock(PeriodKind.EXTRA_SECOND, 1),
        MatchClock(PeriodKind.SHOOTOUT, 0),
    ]
    assert order == sorted(order)
    # strictly increasing
    for a, b in zip(order, order[1:], strict=False):
        assert a < b


def test_stoppage_breaks_tie_within_period():
    regular = MatchClock(PeriodKind.SECOND_HALF, 90 * 60, added=0)
    plus_one = MatchClock(PeriodKind.SECOND_HALF, 90 * 60, added=60)
    assert regular < plus_one


def test_shootout_has_no_added_time():
    with pytest.raises(ValueError):
        MatchClock(PeriodKind.SHOOTOUT, second=0, added=5)


def test_regulation_and_shootout_flags():
    assert MatchClock(PeriodKind.FIRST_HALF, 0).is_regulation
    assert not MatchClock(PeriodKind.EXTRA_FIRST, 0).is_regulation
    assert MatchClock(PeriodKind.SHOOTOUT, 0).is_shootout


def test_monotone_axis_places_later_periods_after():
    fh = MatchClock(PeriodKind.FIRST_HALF, 44 * 60)
    sh = MatchClock(PeriodKind.SECOND_HALF, 1 * 60)
    assert sh.monotone_second() > fh.monotone_second()
