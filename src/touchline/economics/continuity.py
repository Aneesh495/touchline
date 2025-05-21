"""Squad continuity over seasons from registration spells and eligible minutes.

Continuity is more than a headcount: a club that keeps its core eleven but churns
fringe players is more continuous than the raw turnover fraction suggests. This
module computes both a roster-level continuity (players retained) and a
minutes-weighted continuity (share of last season's minutes played by retained
players), so the measure reflects who actually played.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuitySummary:
    season_from: str
    season_to: str
    roster_continuity: float  # fraction of previous squad retained
    minutes_weighted_continuity: float  # share of previous minutes retained
    arrivals: int
    departures: int


def season_continuity(
    prev_minutes: dict[str, float],
    current_squad: set[str],
    season_from: str,
    season_to: str,
) -> ContinuitySummary:
    """Compare a previous season's minutes to the current squad.

    ``prev_minutes`` maps each player to their eligible minutes last season.
    Roster continuity is the fraction of last season's players still present.
    Minutes-weighted continuity is the share of last season's total minutes played
    by players who are still present, which weights the core more heavily.
    """
    prev_players = set(prev_minutes)
    retained = prev_players & current_squad
    departures = prev_players - current_squad
    arrivals = current_squad - prev_players

    roster = len(retained) / len(prev_players) if prev_players else 0.0
    total_minutes = sum(prev_minutes.values())
    retained_minutes = sum(prev_minutes[p] for p in retained)
    minutes_weighted = retained_minutes / total_minutes if total_minutes > 0 else 0.0

    return ContinuitySummary(
        season_from=season_from,
        season_to=season_to,
        roster_continuity=roster,
        minutes_weighted_continuity=minutes_weighted,
        arrivals=len(arrivals),
        departures=len(departures),
    )
