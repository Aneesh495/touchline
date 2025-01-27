"""Sequence action value.

Each action is valued by how it changes the controlling team's chance of scoring
and of conceding within a declared future horizon of actions. This follows the
idea of Decroos et al. ("Actions Speak Louder than Goals", KDD 2019): estimate,
for the game state after an action, the probability that the team in possession
scores within the next ``horizon`` actions and the probability it concedes, then
define the action's value as the change in (score - concede) probability from
before to after the action.

The two probabilities are estimated by logistic models on state features. Labels
are built causally: an action is labelled as leading to a score if a goal by the
acting team occurs within the next ``horizon`` actions, and symmetrically for
conceding. The before/after value is computed consistently, accounting for the
possession change: when possession flips, the "after" state is evaluated from the
new controlling team's perspective, so winning the ball in a dangerous area is
correctly credited.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from touchline.domain.events import Event, EventType
from touchline.models.xg_logistic import LogisticXG


@dataclass
class ActionValueModel:
    horizon: int = 10
    score_model: LogisticXG = field(default_factory=lambda: LogisticXG(epochs=300))
    concede_model: LogisticXG = field(default_factory=lambda: LogisticXG(epochs=300))
    fitted: bool = False

    @staticmethod
    def state_features(ev: Event) -> list[float]:
        """Features of the game state produced by an event.

        Uses only the event's own observable context: the canonical location of
        the ball, the event type one-hots for the most informative types, and the
        period. No future information enters.
        """
        loc = ev.location
        x = loc.x if loc else 0.5
        y = loc.y if loc else 0.5
        dist = ((1.0 - x) ** 2 + (0.5 - y) ** 2) ** 0.5
        return [
            x,
            y,
            dist,
            float(ev.type is EventType.PASS),
            float(ev.type is EventType.CARRY),
            float(ev.type is EventType.SHOT),
            float(ev.type is EventType.DRIBBLE),
            float(ev.clock.period.order),
        ]

    def build_labels(
        self, events: list[Event], goal_flags: list[bool]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build (features, scores_within_horizon, concedes_within_horizon).

        ``goal_flags[i]`` is True when event i is a goal. For each event i, we look
        ahead up to ``horizon`` events. If a goal by the acting team occurs, the
        score label is 1; if a goal by the other team occurs first, the concede
        label is 1. Ties are resolved by whichever goal comes first.
        """
        n = len(events)
        feats = np.array([self.state_features(e) for e in events], dtype=float)
        scores = np.zeros(n)
        concedes = np.zeros(n)
        for i in range(n):
            team = events[i].team
            for j in range(i + 1, min(i + 1 + self.horizon, n)):
                if goal_flags[j]:
                    if events[j].team == team:
                        scores[i] = 1.0
                    else:
                        concedes[i] = 1.0
                    break
        return feats, scores, concedes

    def fit(self, events: list[Event], goal_flags: list[bool]) -> ActionValueModel:
        feats, scores, concedes = self.build_labels(events, goal_flags)
        self.score_model.fit(feats, scores)
        self.concede_model.fit(feats, concedes)
        self.fitted = True
        return self

    def state_value(self, ev: Event) -> float:
        """Score probability minus concede probability for the state after ``ev``."""
        f = np.array([self.state_features(ev)])
        return float(self.score_model.predict_proba(f)[0] - self.concede_model.predict_proba(f)[0])

    def action_values(self, events: list[Event]) -> np.ndarray:
        """Value of each action as the change in state value it produced.

        For action i the value is V(after_i) - V(before_i), where the before state
        is the state after the previous action. When possession flips between the
        previous and current action, the previous state value is negated so it is
        expressed from the current team's perspective before crediting the action.
        """
        n = len(events)
        values = np.zeros(n)
        prev_v = 0.0
        prev_team = None
        for i, ev in enumerate(events):
            v_after = self.state_value(ev)
            if prev_team is None:
                v_before = 0.0
            elif ev.team != prev_team:
                v_before = -prev_v  # perspective flip on turnover
            else:
                v_before = prev_v
            values[i] = v_after - v_before
            prev_v = v_after
            prev_team = ev.team
        return values
