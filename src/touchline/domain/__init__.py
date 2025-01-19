"""Typed football domain core.

This layer owns the vocabulary of the project. Everything above it speaks in these
objects, never in raw provider rows. The key invariants it protects:

* Match time is not a uniform 90-minute clock. A :class:`MatchClock` keeps the
  period, the minute within the period, and added (stoppage) time distinct, so a
  goal in the 90+4th minute of the second half is never confused with the 94th
  minute of a hypothetical single period, and shootout kicks are not regulation
  events.
* Pitch coordinates carry their provider's coordinate system and the attacking
  direction of the team in possession. Transforms to a canonical left-to-right
  frame are explicit and reversible.
* Identifiers remember their provider. A StatsBomb player id and a
  football-data.co.uk team name are different namespaces and are only linked
  through an auditable resolution step.
"""

from touchline.domain.clock import MatchClock, Period, PeriodKind
from touchline.domain.events import BodyPart, Event, EventType, Possession, Shot
from touchline.domain.geometry import AttackDirection, Pitch, Point
from touchline.domain.identifiers import (
    CompetitionId,
    EntityRef,
    MatchId,
    PlayerId,
    Provider,
    TeamId,
)
from touchline.domain.match import (
    Appearance,
    Match,
    ScoreState,
    Team,
    Venue,
)

__all__ = [
    "MatchClock",
    "Period",
    "PeriodKind",
    "Pitch",
    "Point",
    "AttackDirection",
    "CompetitionId",
    "EntityRef",
    "MatchId",
    "PlayerId",
    "Provider",
    "TeamId",
    "Event",
    "EventType",
    "Possession",
    "Shot",
    "BodyPart",
    "Appearance",
    "Match",
    "ScoreState",
    "Team",
    "Venue",
]
