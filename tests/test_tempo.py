"""Possession/tempo metric oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.features.tempo import possession_share, team_tempo

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _ev(i, team, etype, x=0.5):
    return Event(i, MatchClock(PeriodKind.FIRST_HALF, i), etype, team, None, Point(x, 0.5))


def test_possession_share_counts_actions():
    events = [_ev(0, A, EventType.PASS), _ev(1, A, EventType.CARRY), _ev(2, B, EventType.PASS)]
    assert abs(possession_share(events, A) - 2 / 3) < 1e-9
    assert abs(possession_share(events, B) - 1 / 3) < 1e-9


def test_territory_reflects_advanced_actions():
    high = [_ev(i, A, EventType.PASS, x=0.8) for i in range(5)]
    t = team_tempo(high, A)
    assert t.territory > 0.7


def test_ppda_unavailable_without_defensive_events():
    # Team A makes only passes/carries: no defensive actions -> PPDA is None.
    events = [_ev(i, A, EventType.PASS) for i in range(5)] + [
        _ev(5, B, EventType.PASS)
    ]
    t = team_tempo(events, A)
    assert t.ppda is None


def test_ppda_computed_with_defensive_events():
    events = [
        _ev(0, B, EventType.PASS),
        _ev(1, B, EventType.PASS),
        _ev(2, A, EventType.INTERCEPTION),
        _ev(3, A, EventType.DUEL),
    ]
    t = team_tempo(events, A)
    # 2 opponent passes / 2 defensive actions = 1.0 PPDA
    assert t.ppda == 1.0
