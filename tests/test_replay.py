"""Replay timeline oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.features.replay import build_timeline

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _shot(i, team, period, sec, goal):
    return Event(
        i, MatchClock(period, sec), EventType.SHOT, team, None, Point(0.9, 0.5),
        raw={"shot": {"outcome": {"name": "Goal" if goal else "Saved"}}},
    )


def test_timeline_is_time_ordered_and_scores_accumulate():
    events = [
        _shot(0, A, PeriodKind.FIRST_HALF, 10 * 60, goal=True),   # A 1-0
        _shot(1, B, PeriodKind.SECOND_HALF, 20 * 60, goal=True),  # 1-1
        _shot(2, A, PeriodKind.SECOND_HALF, 40 * 60, goal=False), # no change
    ]
    tl = build_timeline(events, home_team=A)
    # non-decreasing monotone time
    times = [f.monotone_second for f in tl]
    assert times == sorted(times)
    # final frame shows 1-1
    assert tl[-1].home_score == 1
    assert tl[-1].away_score == 1


def test_display_time_keeps_stoppage_distinct():
    events = [
        Event(0, MatchClock(PeriodKind.FIRST_HALF, 45 * 60, added=2 * 60),
              EventType.PASS, A, None, Point(0.5, 0.5)),
    ]
    tl = build_timeline(events, home_team=A)
    assert tl[0].display_time == "45+2"


def test_scrubbing_shows_score_at_each_frame():
    events = [
        _shot(0, A, PeriodKind.FIRST_HALF, 5 * 60, goal=True),
        _shot(1, A, PeriodKind.FIRST_HALF, 15 * 60, goal=True),
    ]
    tl = build_timeline(events, home_team=A)
    assert tl[0].home_score == 1  # after the first goal
    assert tl[1].home_score == 2  # after the second
