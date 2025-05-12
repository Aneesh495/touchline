"""Expected-assists oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import BodyPart, Event, EventType, Shot
from touchline.domain.geometry import Point
from touchline.domain.identifiers import PlayerId, Provider, TeamId
from touchline.models.expected_assists import expected_assists, total_xa_by_player

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _p(v):
    return PlayerId(Provider.STATSBOMB, v)


def _ev(i, team, etype, player, x=0.5):
    return Event(i, MatchClock(PeriodKind.FIRST_HALF, i), etype, team, _p(player), Point(x, 0.5))


def _shot(i, team, player, x):
    return Shot(
        event_index=i, clock=MatchClock(PeriodKind.FIRST_HALF, i), team=team,
        player=_p(player), location=Point(x, 0.5), body_part=BodyPart.RIGHT_FOOT,
        is_penalty=False, is_shootout=False, is_goal=False,
    )


def _constant_scorer(v):
    return 0.25  # a fixed xG for any shot, to isolate the crediting logic


def test_pass_before_shot_is_credited():
    events = [
        _ev(0, A, EventType.PASS, "passer", x=0.6),
        _ev(1, A, EventType.SHOT, "shooter", x=0.9),
    ]
    shots = {1: _shot(1, A, "shooter", 0.9)}
    credits = expected_assists(events, shots, _constant_scorer)
    assert len(credits) == 1
    assert credits[0].pass_event_index == 0
    assert credits[0].xa == 0.25


def test_pass_lost_before_shot_not_credited():
    events = [
        _ev(0, A, EventType.PASS, "passer"),
        _ev(1, B, EventType.INTERCEPTION, "b"),
        _ev(2, B, EventType.SHOT, "bshoot", x=0.9),
    ]
    shots = {2: _shot(2, B, "bshoot", 0.9)}
    credits = expected_assists(events, shots, _constant_scorer)
    assert credits == []


def test_total_xa_by_player():
    events = [
        _ev(0, A, EventType.PASS, "p1", x=0.6),
        _ev(1, A, EventType.SHOT, "s1", x=0.9),
        _ev(2, A, EventType.PASS, "p1", x=0.7),
        _ev(3, A, EventType.SHOT, "s2", x=0.85),
    ]
    shots = {1: _shot(1, A, "s1", 0.9), 3: _shot(3, A, "s2", 0.85)}
    totals = total_xa_by_player(events, shots, _constant_scorer)
    assert abs(totals["p1"] - 0.5) < 1e-9  # two key passes * 0.25
