"""SPADL conversion and feature oracles."""

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import PlayerId, Provider, TeamId
from touchline.features.spadl import (
    SpadlResult,
    SpadlType,
    action_state_features,
    feature_dim,
    to_spadl,
)

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _ev(i, team, etype, sx, sy, ex=None, ey=None, success=None):
    return Event(
        i, MatchClock(PeriodKind.FIRST_HALF, i), etype, team,
        PlayerId(Provider.STATSBOMB, f"p{i}"), Point(sx, sy),
        end_location=Point(ex, ey) if ex is not None else None,
        outcome_success=success,
    )


def test_to_spadl_maps_types_and_results():
    events = [
        _ev(0, A, EventType.PASS, 0.3, 0.5, 0.5, 0.5, success=True),
        _ev(1, A, EventType.SHOT, 0.9, 0.5, success=False),
        _ev(2, A, EventType.OTHER, 0.5, 0.5),  # maps to OTHER
    ]
    actions = to_spadl(events)
    assert actions[0].type is SpadlType.PASS
    assert actions[0].result is SpadlResult.SUCCESS
    assert actions[0].movement > 0
    assert actions[1].type is SpadlType.SHOT
    assert actions[1].result is SpadlResult.FAIL
    assert actions[2].type is SpadlType.OTHER


def test_events_without_location_skipped():
    events = [
        Event(0, MatchClock(PeriodKind.FIRST_HALF, 0), EventType.PASS, A, None, None),
        _ev(1, A, EventType.PASS, 0.3, 0.5),
    ]
    actions = to_spadl(events)
    assert len(actions) == 1


def test_feature_vector_has_expected_dim_and_padding():
    events = [_ev(0, A, EventType.PASS, 0.3, 0.5, 0.5, 0.5, success=True)]
    actions = to_spadl(events)
    f = action_state_features(actions, 0, window=3)
    assert len(f) == feature_dim(window=3)
    # with only one action, the three preceding slots are zero-padded
    per = 6 + len(list(SpadlType)) + 1
    assert all(v == 0.0 for v in f[per:])


def test_same_team_flag_reflects_possession_context():
    events = [
        _ev(0, A, EventType.PASS, 0.3, 0.5, 0.4, 0.5, success=True),
        _ev(1, B, EventType.INTERCEPTION, 0.4, 0.5),
    ]
    actions = to_spadl(events)
    # for the interception (current = B), the preceding A action's same-team flag is 0
    f = action_state_features(actions, 1, window=1)
    per = 6 + len(list(SpadlType)) + 1
    # current action block ends with same-team flag 1 (itself)
    assert f[per - 1] == 1.0
    # preceding block's last element (same-team flag) is 0 (A vs B)
    assert f[2 * per - 1] == 0.0
