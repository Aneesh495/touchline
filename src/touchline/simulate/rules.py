"""League table rules: points, tie-breaks, and deductions.

Points are not universal. The three-points-for-a-win rule was adopted at different
times in different leagues (England 1981, most others in the 1990s), so the points
awarded for a win are a parameter, not a constant. Tie-breaks differ too: the
Premier League separates equal points by goal difference then goals scored, while
La Liga uses head-to-head results first. The engine therefore takes an explicit
:class:`LeagueRules` describing the season rather than hardcoding one league's
conventions for all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TieBreak(str, Enum):
    GOAL_DIFFERENCE = "goal_difference"
    GOALS_FOR = "goals_for"
    HEAD_TO_HEAD_POINTS = "h2h_points"
    HEAD_TO_HEAD_GD = "h2h_gd"
    WINS = "wins"


@dataclass(frozen=True)
class LeagueRules:
    points_win: int = 3
    points_draw: int = 1
    points_loss: int = 0
    tie_breaks: tuple[TieBreak, ...] = (
        TieBreak.GOAL_DIFFERENCE,
        TieBreak.GOALS_FOR,
        TieBreak.WINS,
    )
    deductions: dict[str, int] = field(default_factory=dict)


@dataclass
class TableRow:
    team: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


@dataclass(frozen=True)
class Fixture:
    home: str
    away: str
    home_goals: int
    away_goals: int


def _h2h_metrics(team: str, others: set[str], fixtures: list[Fixture], rules: LeagueRules):
    """Points and goal difference for ``team`` restricted to matches vs ``others``."""
    pts = 0
    gd = 0
    for f in fixtures:
        if f.home == team and f.away in others:
            gd += f.home_goals - f.away_goals
            pts += _points_for(f.home_goals, f.away_goals, rules)
        elif f.away == team and f.home in others:
            gd += f.away_goals - f.home_goals
            pts += _points_for(f.away_goals, f.home_goals, rules)
    return pts, gd


def _points_for(gf: int, ga: int, rules: LeagueRules) -> int:
    if gf > ga:
        return rules.points_win
    if gf < ga:
        return rules.points_loss
    return rules.points_draw


def compute_table(
    teams: list[str], fixtures: list[Fixture], rules: LeagueRules
) -> list[TableRow]:
    """Build the ordered league table from fixtures under the given rules."""
    rows = {t: TableRow(t) for t in teams}
    for f in fixtures:
        h, a = rows[f.home], rows[f.away]
        h.played += 1
        a.played += 1
        h.goals_for += f.home_goals
        h.goals_against += f.away_goals
        a.goals_for += f.away_goals
        a.goals_against += f.home_goals
        if f.home_goals > f.away_goals:
            h.won += 1
            a.lost += 1
            h.points += rules.points_win
            a.points += rules.points_loss
        elif f.home_goals < f.away_goals:
            a.won += 1
            h.lost += 1
            a.points += rules.points_win
            h.points += rules.points_loss
        else:
            h.drawn += 1
            a.drawn += 1
            h.points += rules.points_draw
            a.points += rules.points_draw
    for team, pts in rules.deductions.items():
        if team in rows:
            rows[team].points -= pts

    ordered = sorted(rows.values(), key=lambda r: _sort_key(r, fixtures, rows, rules))
    return ordered


def _sort_key(row: TableRow, fixtures: list[Fixture], rows: dict, rules: LeagueRules):
    # Primary: points descending. Negate numeric metrics so ascending sort gives
    # the conventional descending ranking.
    key: list[float] = [-row.points]
    tied = {t for t, r in rows.items() if r.points == row.points}
    for tb in rules.tie_breaks:
        if tb is TieBreak.GOAL_DIFFERENCE:
            key.append(-row.goal_difference)
        elif tb is TieBreak.GOALS_FOR:
            key.append(-row.goals_for)
        elif tb is TieBreak.WINS:
            key.append(-row.won)
        elif tb is TieBreak.HEAD_TO_HEAD_POINTS:
            pts, _ = _h2h_metrics(row.team, tied - {row.team}, fixtures, rules)
            key.append(-pts)
        elif tb is TieBreak.HEAD_TO_HEAD_GD:
            _, gd = _h2h_metrics(row.team, tied - {row.team}, fixtures, rules)
            key.append(-gd)
    key.append(row.team)  # stable final tie-break by name
    return tuple(key)
