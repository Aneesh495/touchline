"""Shot feature extraction for xG models.

Only context known at the instant of the shot is used: the shot location geometry
(distance and angle), the body part, whether it is a penalty, the situation
(open play, set piece, corner, free kick, counter), and whether spatial context
(a freeze frame of defenders) is available. The number of defenders and the
goalkeeper position are included only when a freeze frame actually exists, so
event-only matches do not get fabricated spatial features.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.domain.events import BodyPart, Shot


@dataclass(frozen=True)
class ShotFeatureRow:
    """A flat, model-ready feature row for one shot, plus its label."""

    distance_m: float
    angle_rad: float
    is_header: int
    is_penalty: int
    is_free_kick: int
    is_corner: int
    is_counter: int
    has_spatial: int
    defenders_in_cone: int | None  # None when no freeze frame
    gk_distance_m: float | None  # None when no freeze frame
    is_goal: int

    def dense_vector(self) -> list[float]:
        """The always-available numeric features (spatial ones excluded).

        Spatial features are offered separately so a model trained on event-only
        matches never depends on a value that is missing for most shots.
        """
        return [
            self.distance_m,
            self.angle_rad,
            float(self.is_header),
            float(self.is_penalty),
            float(self.is_free_kick),
            float(self.is_corner),
            float(self.is_counter),
        ]


def _count_defenders_in_cone(shot: Shot) -> tuple[int | None, float | None]:
    """Count defenders roughly between the shot and goal, and goalkeeper distance.

    Uses the freeze frame when present. A defender is "in the cone" when its x is
    ahead of the shot toward goal and its y is within the lateral span to the
    goalposts. This is a simple, documented heuristic, not a claim about the
    provider's own definition.
    """
    ff = shot.raw.get("freeze_frame")
    if not ff:
        return None, None
    sx, sy = shot.location.x, shot.location.y
    defenders = 0
    gk_dist: float | None = None
    for actor in ff:
        loc = actor.get("location")
        if not loc or len(loc) < 2:
            continue
        # freeze-frame coordinates are in the StatsBomb 120x80 frame
        ax, ay = loc[0] / 120.0, loc[1] / 80.0
        teammate = actor.get("teammate", False)
        keeper = actor.get("position", {}).get("name") == "Goalkeeper"
        if keeper and not teammate:
            gk_dist = (((1.0 - ax)) ** 2 + (0.5 - ay) ** 2) ** 0.5 * 100.0
        if not teammate and ax >= sx and abs(ay - sy) <= abs(1.0 - sy) + 0.1:
            defenders += 1
    return defenders, gk_dist


def shot_features(shot: Shot) -> ShotFeatureRow:
    defenders, gk_dist = _count_defenders_in_cone(shot)
    has_spatial = shot.raw.get("freeze_frame") is not None
    return ShotFeatureRow(
        distance_m=shot.location.distance_to_goal_m(),
        angle_rad=shot.location.shot_angle_rad(),
        is_header=int(shot.body_part is BodyPart.HEAD),
        is_penalty=int(shot.is_penalty),
        is_free_kick=int(shot.situation == "free_kick"),
        is_corner=int(shot.situation == "corner"),
        is_counter=int(shot.situation == "counter"),
        has_spatial=int(has_spatial),
        defenders_in_cone=defenders,
        gk_distance_m=gk_dist,
        is_goal=int(shot.is_goal),
    )
