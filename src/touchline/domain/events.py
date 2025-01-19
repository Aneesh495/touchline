"""On-ball events, shots, and possession segments.

These objects are deliberately thin and typed. They carry the canonical location
(when known), the match clock, the acting team and player references, and a
free-form ``raw`` mapping that preserves the original provider payload so no
information is destroyed during canonicalisation. Downstream code must read
canonical fields; ``raw`` exists for audit and for recovering provider specifics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from touchline.domain.clock import MatchClock
from touchline.domain.geometry import Point
from touchline.domain.identifiers import PlayerId, TeamId


class EventType(StrEnum):
    """Canonical event taxonomy.

    Kept small and provider-agnostic. Provider-specific subtypes live in ``raw``.
    """

    PASS = "pass"
    CARRY = "carry"
    SHOT = "shot"
    DRIBBLE = "dribble"
    DUEL = "duel"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    FOUL_COMMITTED = "foul_committed"
    FOUL_WON = "foul_won"
    RECOVERY = "recovery"
    GOAL_KEEPER = "goalkeeper"
    PRESSURE = "pressure"
    CORNER = "corner"
    FREE_KICK = "free_kick"
    PENALTY = "penalty"
    SUBSTITUTION = "substitution"
    CARD = "card"
    OTHER = "other"


class BodyPart(StrEnum):
    RIGHT_FOOT = "right_foot"
    LEFT_FOOT = "left_foot"
    HEAD = "head"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Event:
    """A single on-ball event in canonical form."""

    index: int  # order within the match, 0-based
    clock: MatchClock
    type: EventType
    team: TeamId
    player: PlayerId | None
    location: Point | None
    end_location: Point | None = None
    outcome_success: bool | None = None
    possession_id: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def is_in_regulation(self) -> bool:
        return self.clock.is_regulation


@dataclass(frozen=True)
class Shot:
    """A shot attempt with the fields xG models are allowed to use.

    Only observed context is carried. If the body part or situation is unknown the
    field is UNKNOWN rather than guessed, so missingness strata remain visible to
    evaluation. ``is_penalty`` and ``is_shootout`` separate those contexts because
    their scoring rates and sample handling differ.
    """

    event_index: int
    clock: MatchClock
    team: TeamId
    player: PlayerId | None
    location: Point
    body_part: BodyPart
    is_penalty: bool
    is_shootout: bool
    is_goal: bool
    situation: str = "open_play"  # open_play | set_piece | counter | corner | free_kick
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def counts_toward_regulation(self) -> bool:
        """Shootout kicks are excluded from regulation shot and xG counts."""
        return not self.is_shootout


@dataclass
class Possession:
    """A contiguous spell of control by one team.

    Possession boundaries are produced by the segmenter, not by the provider.
    ``review_flag`` marks edge cases (rebounds, contested restarts, goalkeeper
    control, gaps from missing events) that a human may want to inspect.
    """

    possession_id: int
    team: TeamId
    start_index: int
    end_index: int  # inclusive
    start_clock: MatchClock
    end_clock: MatchClock
    event_count: int
    review_flag: str | None = None

    def __post_init__(self) -> None:
        if self.end_index < self.start_index:
            raise ValueError("possession end precedes start")
        if self.event_count < 1:
            raise ValueError("possession must contain at least one event")
