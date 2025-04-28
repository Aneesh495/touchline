"""Passing network oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import PlayerId, Provider, TeamId
from touchline.features.networks import build_passing_network

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _p(v):
    return PlayerId(Provider.STATSBOMB, v)


def _ev(i, team, etype, player, x=0.5, y=0.5, success=True):
    return Event(
        i, MatchClock(PeriodKind.FIRST_HALF, i), etype, team, _p(player),
        Point(x, y), outcome_success=success,
    )


def test_edge_from_pass_to_next_teammate():
    events = [
        _ev(0, A, EventType.PASS, "p1", x=0.3),
        _ev(1, A, EventType.CARRY, "p2", x=0.5),
        _ev(2, A, EventType.PASS, "p2", x=0.5),
        _ev(3, A, EventType.SHOT, "p3", x=0.9),
    ]
    net = build_passing_network(events, A)
    assert net.edge_count("p1", "p2") == 1
    assert net.edge_count("p2", "p3") == 1
    assert net.total_passes() == 2


def test_pass_lost_to_opponent_makes_no_edge():
    events = [
        _ev(0, A, EventType.PASS, "p1"),
        _ev(1, B, EventType.INTERCEPTION, "b1"),
    ]
    net = build_passing_network(events, A)
    assert net.total_passes() == 0


def test_node_positions_are_mean_locations():
    events = [
        _ev(0, A, EventType.PASS, "p1", x=0.2, y=0.4),
        _ev(1, A, EventType.CARRY, "p1", x=0.4, y=0.6),
    ]
    net = build_passing_network(events, A)
    x, y = net.node_positions["p1"]
    assert abs(x - 0.3) < 1e-9
    assert abs(y - 0.5) < 1e-9
    assert net.node_counts["p1"] == 2
