"""Geometry oracles: hand-computed distances and angles, and flip invariants."""

import math

from touchline.domain.geometry import (
    PITCH_LENGTH_M,
    AttackDirection,
    Pitch,
    Point,
)


def test_penalty_spot_distance():
    # Canonical penalty spot is 11 m from goal, i.e. x = 1 - 11/105 on the centre.
    x = 1.0 - 11.0 / PITCH_LENGTH_M
    p = Point(x, 0.5)
    assert math.isclose(p.distance_to_goal_m(), 11.0, abs_tol=1e-6)


def test_angle_larger_when_closer_and_central():
    close = Point(1.0 - 6.0 / PITCH_LENGTH_M, 0.5)
    far = Point(1.0 - 30.0 / PITCH_LENGTH_M, 0.5)
    assert close.shot_angle_rad() > far.shot_angle_rad()
    # A central position subtends a larger angle than a wide one at equal distance.
    central = Point(1.0 - 18.0 / PITCH_LENGTH_M, 0.5)
    wide = Point(1.0 - 18.0 / PITCH_LENGTH_M, 0.9)
    assert central.shot_angle_rad() > wide.shot_angle_rad()


def test_statsbomb_frame_maps_goal_mouth_to_x1():
    # StatsBomb 120x80, y down. A shot at (120, 40) attacking left-to-right is the
    # goal centre and must land at canonical x ~ 1, y ~ 0.5.
    sb = Pitch(length=120.0, width=80.0, y_down=True)
    p = sb.to_canonical(120.0, 40.0, AttackDirection.LEFT_TO_RIGHT)
    assert math.isclose(p.x, 1.0, abs_tol=1e-9)
    assert math.isclose(p.y, 0.5, abs_tol=1e-9)


def test_direction_flip_maps_both_ends_to_attacking_goal():
    sb = Pitch(length=120.0, width=80.0, y_down=True)
    # Team attacking right-to-left shoots at the x=0 provider end; canonical x -> 1.
    p = sb.to_canonical(0.0, 40.0, AttackDirection.RIGHT_TO_LEFT)
    assert math.isclose(p.x, 1.0, abs_tol=1e-9)
