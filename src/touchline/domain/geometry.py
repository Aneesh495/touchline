"""Pitch geometry and coordinate transforms.

Providers disagree about the pitch frame. StatsBomb uses a 120x80 grid with the
origin at a corner and y increasing downward; football event feeds often use a
100x100 or metric frame; attacking direction flips at half time. A model that
wants "distance to goal" must therefore know which frame a point is in and which
way the team is attacking.

The canonical frame used across Touchline is:

* x in [0, 1] from the attacking team's own goal line (0) to the opponent goal
  line (1),
* y in [0, 1] from the attacking team's left touchline to its right touchline,
* so that a shot near (1.0, 0.5) is a shot from the centre of the six-yard box
  regardless of which physical end the team is attacking.

Transforms into this frame are explicit. This keeps "flipped pitch" bugs, which
the semantic verifier specifically probes for, out of the model inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class AttackDirection(StrEnum):
    """Which way the team in possession is attacking in the provider frame."""

    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"


@dataclass(frozen=True)
class Pitch:
    """A provider pitch frame described by its extents.

    ``length`` and ``width`` are the provider coordinate extents (e.g. 120 and 80
    for StatsBomb). ``y_down`` is True when provider y increases downward.
    """

    length: float
    width: float
    y_down: bool = True

    def __post_init__(self) -> None:
        if self.length <= 0 or self.width <= 0:
            raise ValueError("pitch extents must be positive")

    def to_canonical(self, x: float, y: float, attacking: AttackDirection) -> Point:
        """Map a provider point into the canonical attacking frame.

        The result has x growing toward the goal the possessing team attacks and y
        growing to that team's right. The mapping is a reflection, hence its own
        inverse up to the direction argument.
        """
        nx = x / self.length
        ny = y / self.width
        if attacking is AttackDirection.RIGHT_TO_LEFT:
            nx = 1.0 - nx
            ny = 1.0 - ny
        if self.y_down:
            # provider y grows downward; after any flip, convert to y-up-right
            ny = 1.0 - ny if attacking is AttackDirection.LEFT_TO_RIGHT else ny
        return Point(_clamp01(nx), _clamp01(ny))


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


# Canonical goal mouth, as fractions of the canonical frame. The goal is at x=1,
# centred on y=0.5, and is 7.32 m wide on a nominal 105 m x 68 m pitch.
GOAL_X = 1.0
GOAL_Y = 0.5
GOAL_HALF_WIDTH = (7.32 / 2.0) / 68.0
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0


@dataclass(frozen=True)
class Point:
    """A point in the canonical [0,1]x[0,1] attacking frame."""

    x: float
    y: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.x <= 1.0 and 0.0 <= self.y <= 1.0):
            raise ValueError(f"canonical point out of range: ({self.x}, {self.y})")

    def distance_to_goal_m(self) -> float:
        """Euclidean distance to the goal centre in metres."""
        dx = (GOAL_X - self.x) * PITCH_LENGTH_M
        dy = (GOAL_Y - self.y) * PITCH_WIDTH_M
        return math.hypot(dx, dy)

    def shot_angle_rad(self) -> float:
        """Angle subtended by the goal mouth from this point, in radians.

        A larger angle means more open goal to aim at. This is the standard xG
        geometry feature. When the shot is on the goal line the angle is taken as
        pi (directly facing an open goal) in the limit, and 0 from the corners.
        """
        half_w_m = GOAL_HALF_WIDTH * PITCH_WIDTH_M
        dx = max((GOAL_X - self.x) * PITCH_LENGTH_M, 1e-6)
        dy = (GOAL_Y - self.y) * PITCH_WIDTH_M
        # angle to each post, then the difference
        a1 = math.atan2(dy + half_w_m, dx)
        a2 = math.atan2(dy - half_w_m, dx)
        return abs(a1 - a2)
