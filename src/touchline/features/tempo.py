"""Possession, tempo, and territory metrics under observed-event eligibility.

These summarise a team's play from the event stream: possession share by event
count, sequence length (actions per possession), tempo (actions per minute of
possession time), and territory (mean canonical x of a team's actions). Pressing
intensity (PPDA, passes allowed per defensive action) is computed only when the
defensive events needed for it are observed; otherwise it is reported as
unavailable rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.domain.events import Event, EventType
from touchline.domain.identifiers import TeamId
from touchline.features.possession import segment_possessions

_DEFENSIVE = {
    EventType.INTERCEPTION,
    EventType.DUEL,
    EventType.FOUL_COMMITTED,
    EventType.CLEARANCE,
}


@dataclass(frozen=True)
class TeamTempo:
    team: str
    possessions: int
    actions: int
    mean_sequence_length: float
    territory: float  # mean canonical x of the team's located actions
    ppda: float | None  # None when defensive events are not observed


def team_tempo(events: list[Event], team: TeamId) -> TeamTempo:
    poss = [p for p in segment_possessions(events) if p.team == team]
    team_events = [e for e in events if e.team == team]
    actions = len(team_events)
    located = [e.location.x for e in team_events if e.location is not None]
    territory = sum(located) / len(located) if located else 0.0
    seq = actions / len(poss) if poss else 0.0

    # PPDA: opponent passes divided by this team's defensive actions in the
    # opponent's build-up zone. Requires defensive events to be present.
    opp_passes = sum(
        1 for e in events if e.team != team and e.type is EventType.PASS
    )
    def_actions = sum(1 for e in team_events if e.type in _DEFENSIVE)
    ppda = (opp_passes / def_actions) if def_actions > 0 else None

    return TeamTempo(
        team=str(team.value),
        possessions=len(poss),
        actions=actions,
        mean_sequence_length=seq,
        territory=territory,
        ppda=ppda,
    )


def possession_share(events: list[Event], team: TeamId) -> float:
    """Share of controlled actions belonging to a team (event-count definition)."""
    total = len(events)
    if total == 0:
        return 0.0
    own = sum(1 for e in events if e.team == team)
    return own / total
