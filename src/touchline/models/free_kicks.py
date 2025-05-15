"""Free-kick and corner delivery classification and conversion.

Free kicks are not all the same: a direct shooting free kick, a crossing free kick,
and a short restart are different processes. A foul does not always produce a
recorded free kick because of advantage, so the count of free kicks is not the count
of fouls; this module keeps them distinct. Corner deliveries are classified by their
end location into inswinging, outswinging, or short, where the trajectory is
observable, and reported as unknown otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from touchline.domain.events import Event
from touchline.domain.geometry import Point


class FreeKickType(str, Enum):
    DIRECT_SHOT = "direct_shot"
    CROSS = "cross"
    SHORT = "short"
    UNKNOWN = "unknown"


def classify_free_kick(location: Point, end: Point | None, took_shot: bool) -> FreeKickType:
    """Classify a free kick from its location, end, and whether a shot was taken.

    A shot from the free kick is a direct-shot type. Otherwise, a delivery ending in
    the box is a cross and a short pass nearby is a short restart. Without an end
    location the type is unknown rather than guessed.
    """
    if took_shot:
        return FreeKickType.DIRECT_SHOT
    if end is None:
        return FreeKickType.UNKNOWN
    travelled = ((end.x - location.x) ** 2 + (end.y - location.y) ** 2) ** 0.5
    ended_in_box = end.x > 0.83 and 0.21 < end.y < 0.79
    if ended_in_box and travelled > 0.12:
        return FreeKickType.CROSS
    return FreeKickType.SHORT


class CornerDelivery(str, Enum):
    INSWINGER = "inswinger"
    OUTSWINGER = "outswinger"
    SHORT = "short"
    UNKNOWN = "unknown"


def classify_corner(from_left: bool, end: Point | None, trajectory_known: bool) -> CornerDelivery:
    """Classify a corner delivery when the trajectory is observable.

    An inswinger curves toward the goal, an outswinger away; which one depends on
    the corner side and the delivering foot, which is only known when the trajectory
    data exists. Without it the delivery is unknown rather than guessed. A short
    corner is recognised by an end location near the corner flag.
    """
    if end is None:
        return CornerDelivery.UNKNOWN
    near_corner = end.x < 0.9 and (end.y < 0.15 or end.y > 0.85)
    if near_corner:
        return CornerDelivery.SHORT
    if not trajectory_known:
        return CornerDelivery.UNKNOWN
    # curving toward goal centre from the near side is an inswinger
    toward_centre = abs(end.y - 0.5) < 0.25
    return CornerDelivery.INSWINGER if toward_centre else CornerDelivery.OUTSWINGER


@dataclass(frozen=True)
class FreeKickCounts:
    fouls: int
    free_kicks_recorded: int

    def discrepancy(self) -> int:
        """Fouls not resulting in a recorded free kick (advantage, etc.).

        Non-negative by football logic; a negative value signals a data problem and
        is surfaced as such by the caller.
        """
        return self.fouls - self.free_kicks_recorded


def free_kick_from_event(ev: Event, took_shot: bool) -> FreeKickType:
    end = ev.end_location
    if ev.location is None:
        return FreeKickType.UNKNOWN
    return classify_free_kick(ev.location, end, took_shot)
