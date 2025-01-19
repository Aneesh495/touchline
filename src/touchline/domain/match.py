"""Match, team, venue, appearance, and score-state objects.

A :class:`Match` is the top-level container. It knows its competition and season,
the two teams, the venue, the final score split by phase (regulation / extra time
/ shootout), the player appearances with their minute intervals, and, when event
data exists, the ordered events and derived possessions.

The score is stored per phase so that, for example, a 1-1 after 90 minutes decided
3-1 on penalties is represented exactly, never flattened to a single "4-2".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from touchline.domain.clock import MatchClock
from touchline.domain.events import Event, Possession, Shot
from touchline.domain.identifiers import CompetitionId, MatchId, PlayerId, TeamId


@dataclass(frozen=True)
class Venue:
    name: str | None
    neutral: bool = False


@dataclass(frozen=True)
class Team:
    team_id: TeamId
    name: str


@dataclass(frozen=True)
class Appearance:
    """A player's participation interval within a match.

    ``start_minute`` and ``end_minute`` are in match-monotone minutes derived from
    the clock. A player who starts and plays the full 90 has (0, 90). A substitute
    who comes on in the 70th has (70, 90). Eligible minutes exclude time the player
    was not on the pitch, which matters for every per-90 denominator.
    """

    player: PlayerId
    team: TeamId
    started: bool
    start_minute: float
    end_minute: float

    @property
    def eligible_minutes(self) -> float:
        return max(0.0, self.end_minute - self.start_minute)


@dataclass(frozen=True)
class ScoreState:
    """Goals by phase. Shootout goals are kept apart from regulation/extra time."""

    home_regulation: int
    away_regulation: int
    home_extra: int = 0
    away_extra: int = 0
    home_shootout: int = 0
    away_shootout: int = 0

    @property
    def home_total_regulation_et(self) -> int:
        return self.home_regulation + self.home_extra

    @property
    def away_total_regulation_et(self) -> int:
        return self.away_regulation + self.away_extra

    def result_char(self) -> str:
        """'H', 'A', or 'D' by regulation+ET score, ignoring any shootout.

        For a league fixture this is the result that decides points. For a knockout
        decided on penalties the shootout winner is a separate question handled by
        the rules engine, not by this character.
        """
        h = self.home_total_regulation_et
        a = self.away_total_regulation_et
        return "H" if h > a else "A" if a > h else "D"


@dataclass
class Match:
    match_id: MatchId
    competition: CompetitionId
    season: str  # e.g. "2021-2022"
    kickoff: date | None
    home: Team
    away: Team
    venue: Venue
    score: ScoreState
    appearances: list[Appearance] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    possessions: list[Possession] = field(default_factory=list)
    shots: list[Shot] = field(default_factory=list)

    @property
    def has_event_data(self) -> bool:
        return len(self.events) > 0

    @property
    def has_spatial_data(self) -> bool:
        """True when any event carries a freeze-frame of other players.

        Spatial (360 / tracking) context is rare. Code that needs it must check
        this flag; off-ball valuation is forbidden when it is False.
        """
        return any(e.raw.get("freeze_frame") for e in self.events)

    def last_clock(self) -> MatchClock | None:
        return self.events[-1].clock if self.events else None
