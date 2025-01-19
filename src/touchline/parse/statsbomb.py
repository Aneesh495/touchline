"""Parser for the StatsBomb / Hudl open-data JSON schema.

The schema (as published at github.com/hudl/open-data) uses a 120x80 pitch with
the origin at the top-left corner and y increasing downward. Each event carries
``period`` (1,2 for halves, 3,4 for extra time, 5 for a shootout), ``minute`` and
``second`` within the period, a ``type.name``, a ``team``, a ``possession`` index,
and optional ``location``. Shots carry ``shot.outcome``, ``shot.body_part``,
``shot.type`` (Open Play / Penalty / Free Kick / Corner / Kick Off) and a
``shot.freeze_frame`` listing other players' positions when 360 data exists.

This module maps those into :mod:`touchline.domain` objects without discarding the
original payload. The mapping of ``period`` to :class:`PeriodKind` is explicit so
extra time and shootouts never collapse into regulation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import BodyPart, Event, EventType, Shot
from touchline.domain.geometry import AttackDirection, Pitch, Point
from touchline.domain.identifiers import Provider, TeamId

SB_PITCH = Pitch(length=120.0, width=80.0, y_down=True)

_PERIOD_MAP = {
    1: PeriodKind.FIRST_HALF,
    2: PeriodKind.SECOND_HALF,
    3: PeriodKind.EXTRA_FIRST,
    4: PeriodKind.EXTRA_SECOND,
    5: PeriodKind.SHOOTOUT,
}

_TYPE_MAP = {
    "Pass": EventType.PASS,
    "Carry": EventType.CARRY,
    "Shot": EventType.SHOT,
    "Dribble": EventType.DRIBBLE,
    "Duel": EventType.DUEL,
    "Interception": EventType.INTERCEPTION,
    "Clearance": EventType.CLEARANCE,
    "Foul Committed": EventType.FOUL_COMMITTED,
    "Foul Won": EventType.FOUL_WON,
    "Ball Recovery": EventType.RECOVERY,
    "Goal Keeper": EventType.GOAL_KEEPER,
    "Pressure": EventType.PRESSURE,
    "Substitution": EventType.SUBSTITUTION,
}

_BODY_PART_MAP = {
    "Right Foot": BodyPart.RIGHT_FOOT,
    "Left Foot": BodyPart.LEFT_FOOT,
    "Head": BodyPart.HEAD,
}


@dataclass(frozen=True)
class StatsBombCompetition:
    competition_id: int
    season_id: int
    competition_name: str
    season_name: str
    country_name: str
    has_360: bool


def parse_statsbomb_competitions(data: bytes | str) -> list[StatsBombCompetition]:
    rows = _load(data)
    out = []
    for r in rows:
        out.append(
            StatsBombCompetition(
                competition_id=int(r["competition_id"]),
                season_id=int(r["season_id"]),
                competition_name=str(r["competition_name"]),
                season_name=str(r["season_name"]),
                country_name=str(r.get("country_name", "")),
                has_360=r.get("match_available_360") is not None,
            )
        )
    return out


def _clock(period: int, minute: int, second: int) -> MatchClock:
    kind = _PERIOD_MAP.get(period, PeriodKind.FIRST_HALF)
    if kind.is_shootout:
        return MatchClock(kind, second=0)
    total = minute * 60 + second
    nominal = kind.nominal_seconds
    # Offsets within a period accumulate from zero at the period start. StatsBomb
    # minute is measured from match start, so subtract the nominal starts of
    # earlier periods to get seconds within this period, then split stoppage time.
    start_minute = {
        PeriodKind.FIRST_HALF: 0,
        PeriodKind.SECOND_HALF: 45,
        PeriodKind.EXTRA_FIRST: 90,
        PeriodKind.EXTRA_SECOND: 105,
    }[kind]
    within = total - start_minute * 60
    if within <= nominal:
        return MatchClock(kind, second=max(0, within))
    return MatchClock(kind, second=nominal, added=within - nominal)


def _point(loc: list | None, attacking: AttackDirection) -> Point | None:
    if not loc or len(loc) < 2:
        return None
    return SB_PITCH.to_canonical(float(loc[0]), float(loc[1]), attacking)


def parse_statsbomb_events(
    data: bytes | str,
    home_team_id: int | None = None,
) -> tuple[list[Event], list[Shot]]:
    """Parse an events file into canonical events and shots.

    Attacking direction is not stored per event by StatsBomb; the convention is
    that each team attacks a consistent direction that flips at half time. Without
    a lineup/direction feed we use a stable per-team assignment (home attacks
    left-to-right in the first half) so the canonical frame is internally
    consistent. The raw payload is preserved for any later direction correction.
    """
    rows = _load(data)
    events: list[Event] = []
    shots: list[Shot] = []
    for r in rows:
        type_name = r.get("type", {}).get("name", "Other")
        team = r.get("team", {})
        team_id = TeamId(Provider.STATSBOMB, str(team.get("id")))
        period = int(r.get("period", 1))
        attacking = _attack_direction(int(team.get("id", 0)), home_team_id, period)
        clock = _clock(period, int(r.get("minute", 0)), int(r.get("second", 0)))
        loc = _point(r.get("location"), attacking)
        etype = _TYPE_MAP.get(type_name, EventType.OTHER)
        player = r.get("player")
        from touchline.domain.identifiers import PlayerId

        pid = (
            PlayerId(Provider.STATSBOMB, str(player["id"]))
            if player and "id" in player
            else None
        )
        ev = Event(
            index=int(r.get("index", len(events))),
            clock=clock,
            type=etype,
            team=team_id,
            player=pid,
            location=loc,
            possession_id=r.get("possession"),
            raw=r,
        )
        events.append(ev)

        if type_name == "Shot" and loc is not None:
            shot = r.get("shot", {})
            outcome = shot.get("outcome", {}).get("name", "")
            sb_type = shot.get("type", {}).get("name", "Open Play")
            shots.append(
                Shot(
                    event_index=ev.index,
                    clock=clock,
                    team=team_id,
                    player=pid,
                    location=loc,
                    body_part=_BODY_PART_MAP.get(
                        shot.get("body_part", {}).get("name", ""), BodyPart.UNKNOWN
                    ),
                    is_penalty=(sb_type == "Penalty"),
                    is_shootout=clock.is_shootout,
                    is_goal=(outcome == "Goal"),
                    situation=_situation(sb_type, r.get("play_pattern", {}).get("name", "")),
                    raw={"shot": shot, "freeze_frame": shot.get("freeze_frame")},
                )
            )
    return events, shots


def _situation(sb_type: str, play_pattern: str) -> str:
    if sb_type == "Penalty":
        return "penalty"
    if sb_type in ("Free Kick",):
        return "free_kick"
    if sb_type == "Corner" or play_pattern == "From Corner":
        return "corner"
    if play_pattern in ("From Free Kick", "From Throw In", "From Keeper"):
        return "set_piece"
    if play_pattern == "From Counter":
        return "counter"
    return "open_play"


def _attack_direction(
    team_id: int, home_team_id: int | None, period: int
) -> AttackDirection:
    is_home = home_team_id is not None and team_id == home_team_id
    first_half_ltr = is_home
    if period in (2, 4):  # direction flips in the second half of each phase
        first_half_ltr = not first_half_ltr
    return (
        AttackDirection.LEFT_TO_RIGHT if first_half_ltr else AttackDirection.RIGHT_TO_LEFT
    )


def parse_statsbomb_match(match_row: dict[str, Any]) -> dict[str, Any]:
    """Extract the summary fields from a StatsBomb matches-file entry.

    Returned as a plain dict of canonical-ready fields; the caller assembles the
    full :class:`~touchline.domain.match.Match` once events are attached.
    """
    return {
        "match_id": str(match_row["match_id"]),
        "home_team_id": int(match_row["home_team"]["home_team_id"]),
        "away_team_id": int(match_row["away_team"]["away_team_id"]),
        "home_team_name": match_row["home_team"]["home_team_name"],
        "away_team_name": match_row["away_team"]["away_team_name"],
        "home_score": int(match_row["home_score"]),
        "away_score": int(match_row["away_score"]),
        "match_date": match_row.get("match_date"),
        "competition": match_row.get("competition", {}).get("competition_name"),
        "season": match_row.get("season", {}).get("season_name"),
    }


def _load(data: bytes | str) -> list[dict]:
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    parsed = json.loads(data)
    if not isinstance(parsed, list):
        raise ValueError("expected a JSON array at top level")
    return parsed
