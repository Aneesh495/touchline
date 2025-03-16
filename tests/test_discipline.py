"""Discipline and manpower-state oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.identifiers import Provider, TeamId
from touchline.models.discipline import (
    ManpowerState,
    post_dismissal_window,
    track_manpower,
)

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _card(index, team, red=True):
    return Event(
        index=index,
        clock=MatchClock(PeriodKind.SECOND_HALF, index),
        type=EventType.CARD,
        team=team,
        player=None,
        location=None,
        raw={"card": {"name": "Red Card" if red else "Yellow Card"}},
    )


def _pass(index, team):
    return Event(
        index=index,
        clock=MatchClock(PeriodKind.SECOND_HALF, index),
        type=EventType.PASS,
        team=team,
        player=None,
        location=None,
    )


def test_manpower_differential():
    s = ManpowerState(11, 10)
    assert s.differential(home=True) == 1
    assert s.differential(home=False) == -1


def test_track_manpower_applies_only_reds():
    events = [
        _pass(0, A),
        _card(1, A, red=False),  # yellow: no change
        _card(2, B, red=True),  # B down to 10
        _pass(3, A),
        _card(4, B, red=True),  # B down to 9
    ]
    timeline = track_manpower(events, home_team=A)
    assert len(timeline) == 2
    assert timeline[0][1].away_players == 10
    assert timeline[1][1].away_players == 9
    assert timeline[1][1].home_players == 11


def test_post_dismissal_window():
    events = [_pass(i, A) for i in range(10)]
    window = post_dismissal_window(events, dismissal_index=2, window=3)
    assert [e.index for e in window] == [3, 4, 5]
