"""Pass-completion and progression models.

Two related targets, each with an explicit denominator:

* Completion: given a pass's geometry and context, the probability it is completed.
  The denominator is attempted passes; the label is completion.
* Progression value: whether a completed pass advances the ball toward the goal by
  a declared threshold. This separates accurate passers from progressive ones,
  which is hypothesis H3.

Both are logistic models on pass features (start and end location, length,
direction toward goal, and whether the pass is under pressure when that is
observed). The project owns the target definitions and the temporal protocol; the
logistic fit is the same gradient-descent estimator used for xG.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from touchline.domain.events import Event, EventType
from touchline.models.xg_logistic import LogisticXG

# A pass is "progressive" when it advances the ball toward the goal by at least this
# fraction of the remaining distance to the goal line. Declared, not discovered.
PROGRESSION_THRESHOLD = 0.10


@dataclass(frozen=True)
class PassFeatures:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    length: float
    forward_gain: float  # end_x - start_x in canonical frame (toward goal)

    def vector(self) -> list[float]:
        return [
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            self.length,
            self.forward_gain,
        ]


def pass_features(ev: Event) -> PassFeatures | None:
    """Extract pass features from a PASS event with a start and end location."""
    if ev.type is not EventType.PASS or ev.location is None:
        return None
    end = ev.end_location or ev.location
    sx, sy = ev.location.x, ev.location.y
    ex, ey = end.x, end.y
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    return PassFeatures(sx, sy, ex, ey, length, ex - sx)


def is_progressive(f: PassFeatures) -> bool:
    """A completed pass that advances a declared fraction toward the goal line."""
    remaining = max(1.0 - f.start_x, 1e-6)
    return f.forward_gain >= PROGRESSION_THRESHOLD * remaining


@dataclass
class PassCompletionModel:
    model: LogisticXG = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.model is None:
            self.model = LogisticXG(epochs=300)

    def fit(self, features: list[PassFeatures], completed: np.ndarray) -> PassCompletionModel:
        x = np.array([f.vector() for f in features], dtype=float)
        self.model.fit(x, np.asarray(completed, dtype=float))
        return self

    def predict(self, features: list[PassFeatures]) -> np.ndarray:
        x = np.array([f.vector() for f in features], dtype=float)
        return self.model.predict_proba(x)
