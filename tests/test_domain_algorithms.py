"""Possession, expected threat, and action-value oracles."""

import numpy as np

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.features.possession import segment_possessions
from touchline.models.action_value import ActionValueModel
from touchline.models.expected_threat import ExpectedThreatGrid

A = TeamId(Provider.STATSBOMB, "A")
B = TeamId(Provider.STATSBOMB, "B")


def _ev(i, team, etype, x=0.5, y=0.5, period=PeriodKind.FIRST_HALF, sec=None):
    return Event(
        index=i,
        clock=MatchClock(period, sec if sec is not None else i * 10),
        type=etype,
        team=team,
        player=None,
        location=Point(x, y),
    )


def test_possession_switches_on_control_change():
    events = [
        _ev(0, A, EventType.PASS),
        _ev(1, A, EventType.CARRY),
        _ev(2, B, EventType.PASS),  # B gains control -> new possession
        _ev(3, B, EventType.SHOT),
    ]
    poss = segment_possessions(events)
    assert len(poss) == 2
    assert poss[0].team == A and poss[0].event_count == 2
    assert poss[1].team == B and poss[1].event_count == 2


def test_contested_event_does_not_switch_possession():
    events = [
        _ev(0, A, EventType.PASS),
        _ev(1, B, EventType.PRESSURE),  # contested, no switch
        _ev(2, A, EventType.CARRY),
    ]
    poss = segment_possessions(events)
    assert len(poss) == 1
    assert poss[0].team == A


def test_period_boundary_flagged():
    events = [
        _ev(0, A, EventType.PASS, period=PeriodKind.FIRST_HALF),
        _ev(1, A, EventType.CARRY, period=PeriodKind.SECOND_HALF, sec=10),
    ]
    poss = segment_possessions(events)
    assert len(poss) == 2
    assert poss[1].review_flag == "period_boundary"


def test_goalkeeper_control_flagged():
    events = [
        _ev(0, A, EventType.SHOT),
        _ev(1, B, EventType.GOAL_KEEPER),
        _ev(2, B, EventType.PASS),
    ]
    poss = segment_possessions(events)
    # B's possession begins at the goalkeeper action.
    b_poss = [p for p in poss if p.team == B]
    assert b_poss and b_poss[0].review_flag in ("goalkeeper_control", "rebound_after_shot")


def test_expected_threat_converges_and_values_advanced_cells_higher():
    grid = ExpectedThreatGrid(n_x=8, n_y=6)
    c = grid.n_cells
    # Build synthetic counts: cells near the goal (high ix) shoot more and score more.
    shoot_counts = np.zeros(c)
    move_counts = np.zeros(c)
    goals = np.zeros(c)
    shots = np.zeros(c)
    move_trans = np.zeros((c, c))
    for ix in range(grid.n_x):
        for iy in range(grid.n_y):
            z = ix * grid.n_y + iy
            advance = ix / grid.n_x
            shoot_counts[z] = 50 * advance
            move_counts[z] = 50 * (1 - advance) + 5
            shots[z] = shoot_counts[z]
            goals[z] = shots[z] * (0.05 + 0.3 * advance)
            # moves tend to go one cell forward
            fwd = min(ix + 1, grid.n_x - 1) * grid.n_y + iy
            move_trans[z, fwd] = move_counts[z] * 0.9
            move_trans[z, z] = move_counts[z] * 0.1
    grid.fit(shoot_counts, move_counts, goals, shots, move_trans)
    assert grid.converged_iters >= 1
    # A central cell near the goal is worth more than one near own end.
    near_goal = grid.value_at(0.95, 0.5)
    near_own = grid.value_at(0.1, 0.5)
    assert near_goal > near_own
    # Values are probabilities in [0, 1].
    assert np.all(grid.value >= -1e-9) and np.all(grid.value <= 1.0 + 1e-6)


def test_action_value_credits_progression_toward_goal():
    rng = np.random.default_rng(1)
    events = []
    goal_flags = []
    # Build sequences that march toward goal and sometimes score, so the score
    # model learns that advanced states precede goals.
    idx = 0
    for _ in range(600):
        team = A
        # Each sequence starts somewhere on the pitch and advances; a goal at the
        # final action is more likely the further the sequence reached, so a
        # carry's own x position genuinely predicts a goal within the horizon.
        start = rng.uniform(0.1, 0.6)
        for step in range(6):
            x = min(start + 0.07 * step, 1.0)
            etype = EventType.SHOT if step == 5 else EventType.CARRY
            events.append(_ev(idx, team, etype, x=x))
            # goal probability grows with how advanced the final shot is
            scored = step == 5 and rng.uniform() < (0.05 + 0.6 * x)
            goal_flags.append(scored)
            idx += 1
    model = ActionValueModel(horizon=6).fit(events, goal_flags)
    assert model.fitted
    # loss must decrease during fitting (real learning)
    assert model.score_model.loss_history[-1] < model.score_model.loss_history[0]
    # State near goal should have higher score-minus-concede value than midfield.
    near = model.state_value(_ev(0, A, EventType.CARRY, x=0.95))
    mid = model.state_value(_ev(0, A, EventType.CARRY, x=0.45))
    assert near > mid
