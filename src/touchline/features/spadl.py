"""SPADL-style unified action representation and its feature construction.

SPADL (Soccer Player Action Description Language) is a provider-agnostic way to
describe on-ball actions with a small, uniform schema: each action has a type, a
start and end location, a result (success or failure), a body part, and the acting
team and player. Converting heterogeneous provider events into this uniform form is
what lets an action-value model treat a StatsBomb pass and a different provider's
pass identically.

This module converts canonical :class:`~touchline.domain.events.Event` objects into
SPADL actions and builds the game-state features the action-value model consumes.
The feature set follows the VAEP formulation: for each action, features describe the
action itself and a short window of preceding actions, so the model sees the
sequence context that gives an action its value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from touchline.domain.events import Event, EventType
from touchline.domain.geometry import Point


class SpadlType(str, Enum):
    PASS = "pass"
    CROSS = "cross"
    DRIBBLE = "dribble"
    CARRY = "carry"
    SHOT = "shot"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    FOUL = "foul"
    KEEPER = "keeper_action"
    OTHER = "other"


class SpadlResult(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    UNKNOWN = "unknown"


_TYPE_MAP = {
    EventType.PASS: SpadlType.PASS,
    EventType.CARRY: SpadlType.CARRY,
    EventType.DRIBBLE: SpadlType.DRIBBLE,
    EventType.SHOT: SpadlType.SHOT,
    EventType.INTERCEPTION: SpadlType.INTERCEPTION,
    EventType.CLEARANCE: SpadlType.CLEARANCE,
    EventType.FOUL_COMMITTED: SpadlType.FOUL,
    EventType.GOAL_KEEPER: SpadlType.KEEPER,
    EventType.DUEL: SpadlType.TACKLE,
}


@dataclass(frozen=True)
class SpadlAction:
    index: int
    type: SpadlType
    team: str
    player: str | None
    start: Point
    end: Point
    result: SpadlResult
    period_order: int

    @property
    def dx(self) -> float:
        return self.end.x - self.start.x

    @property
    def dy(self) -> float:
        return self.end.y - self.start.y

    @property
    def movement(self) -> float:
        return (self.dx**2 + self.dy**2) ** 0.5


def to_spadl(events: list[Event]) -> list[SpadlAction]:
    """Convert canonical events into SPADL actions.

    Events without a location are skipped (SPADL actions are spatial). The end
    location defaults to the start when the provider does not record one.
    """
    actions: list[SpadlAction] = []
    for ev in events:
        if ev.location is None:
            continue
        stype = _TYPE_MAP.get(ev.type, SpadlType.OTHER)
        end = ev.end_location or ev.location
        if ev.outcome_success is True:
            result = SpadlResult.SUCCESS
        elif ev.outcome_success is False:
            result = SpadlResult.FAIL
        else:
            result = SpadlResult.UNKNOWN
        actions.append(
            SpadlAction(
                index=ev.index,
                type=stype,
                team=str(ev.team.value),
                player=ev.player.value if ev.player else None,
                start=ev.location,
                end=end,
                result=result,
                period_order=ev.clock.period.order,
            )
        )
    return actions


# One-hot order for SPADL action types in the feature vector.
_SPADL_ORDER = list(SpadlType)


def action_state_features(actions: list[SpadlAction], i: int, window: int = 3) -> list[float]:
    """VAEP-style features for action i: itself plus a short preceding window.

    The feature vector concatenates, for the current action and up to ``window``
    preceding actions of the same possession-ish context: start x/y, end x/y,
    movement, a type one-hot, and a same-team flag relative to the current action.
    Missing earlier actions (at the start of the match) are zero-padded.
    """
    feats: list[float] = []
    current = actions[i]
    for back in range(window + 1):
        j = i - back
        if j < 0:
            feats.extend([0.0] * (6 + len(_SPADL_ORDER) + 1))
            continue
        a = actions[j]
        feats.extend([a.start.x, a.start.y, a.end.x, a.end.y, a.movement, float(a.result is SpadlResult.SUCCESS)])
        onehot = [1.0 if a.type is t else 0.0 for t in _SPADL_ORDER]
        feats.extend(onehot)
        feats.append(1.0 if a.team == current.team else 0.0)
    return feats


def feature_dim(window: int = 3) -> int:
    """The length of the action_state_features vector for a given window."""
    per_action = 6 + len(_SPADL_ORDER) + 1
    return per_action * (window + 1)
