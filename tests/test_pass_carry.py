"""Pass and carry model oracles."""

import numpy as np

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.models.carry_model import carry_gain, dribble_outcomes
from touchline.models.pass_model import (
    PassCompletionModel,
    is_progressive,
    pass_features,
)

A = TeamId(Provider.STATSBOMB, "A")


def _pass(sx, sy, ex, ey, success=True):
    return Event(
        index=0,
        clock=MatchClock(PeriodKind.FIRST_HALF, 60),
        type=EventType.PASS,
        team=A,
        player=None,
        location=Point(sx, sy),
        end_location=Point(ex, ey),
        outcome_success=success,
    )


def test_pass_features_and_progression():
    f = pass_features(_pass(0.3, 0.5, 0.6, 0.5))
    assert f is not None
    assert f.forward_gain > 0
    assert is_progressive(f)  # gains 0.3 of a remaining 0.7
    # a sideways pass is not progressive
    flat = pass_features(_pass(0.3, 0.2, 0.3, 0.8))
    assert not is_progressive(flat)


def test_pass_completion_learns_distance_effect():
    rng = np.random.default_rng(0)
    feats = []
    labels = []
    for _ in range(2000):
        sx, sy = rng.uniform(0, 1, 2)
        length = rng.uniform(0.02, 0.6)
        angle = rng.uniform(0, 6.28)
        ex = min(max(sx + length * np.cos(angle), 0), 1)
        ey = min(max(sy + length * np.sin(angle), 0), 1)
        f = pass_features(_pass(sx, sy, ex, ey))
        feats.append(f)
        # longer passes complete less often
        p = 1 / (1 + np.exp(-(2.5 - 6 * f.length)))
        labels.append(1.0 if rng.uniform() < p else 0.0)
    model = PassCompletionModel().fit(feats, np.array(labels))
    short = model.predict([pass_features(_pass(0.4, 0.5, 0.45, 0.5))])[0]
    long = model.predict([pass_features(_pass(0.2, 0.5, 0.8, 0.5))])[0]
    assert short > long


def test_carry_gain_from_endpoints_only():
    ev = Event(
        index=0,
        clock=MatchClock(PeriodKind.FIRST_HALF, 60),
        type=EventType.CARRY,
        team=A,
        player=None,
        location=Point(0.4, 0.5),
        end_location=Point(0.7, 0.55),
    )
    g = carry_gain(ev)
    assert g is not None
    assert abs(g.forward_gain - 0.3) < 1e-9
    assert g.is_progressive


def test_dribble_outcomes_count_attempts_and_success():
    events = [
        Event(0, MatchClock(PeriodKind.FIRST_HALF, 1), EventType.DRIBBLE, A, None, Point(0.5, 0.5), outcome_success=True),
        Event(1, MatchClock(PeriodKind.FIRST_HALF, 2), EventType.DRIBBLE, A, None, Point(0.5, 0.5), outcome_success=False),
        Event(2, MatchClock(PeriodKind.FIRST_HALF, 3), EventType.DRIBBLE, A, None, Point(0.5, 0.5), outcome_success=None),
    ]
    out = dribble_outcomes(events)
    assert out.attempts == 3
    assert out.successes == 1
    assert abs(out.success_rate - 1 / 3) < 1e-9
