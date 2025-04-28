"""Strength of schedule and opponent-adjusted performance.

Raw points understate or overstate a team depending on whom it played. Strength of
schedule is the average opponent strength a team faced; opponent-adjusted
performance compares a team's results to what an average team would be expected to
achieve against the same opponents. Both use the opponents known as of the matches
played, so no future fixture leaks in.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.features.team_strength import MatchRow


@dataclass(frozen=True)
class ScheduleSummary:
    team: str
    matches: int
    mean_opponent_strength: float
    points: int
    expected_points_vs_schedule: float

    @property
    def over_performance(self) -> float:
        """Actual minus expected points given the schedule faced."""
        return self.points - self.expected_points_vs_schedule


def _result_points(gf: int, ga: int) -> int:
    return 3 if gf > ga else 1 if gf == ga else 0


def strength_of_schedule(
    matches: list[MatchRow],
    team: str,
    strength: dict[str, float],
    avg_win_prob,
) -> ScheduleSummary:
    """Summarise a team's schedule strength and opponent-adjusted points.

    ``strength`` maps team to a strength scalar (e.g. final Elo). ``avg_win_prob``
    maps a strength differential to an expected points-per-match for an average
    team facing that opponent, so expected points reflect the schedule, not the
    team itself.
    """
    opp_strengths = []
    points = 0
    expected = 0.0
    for m in matches:
        if m.home == team:
            opp = m.away
            points += _result_points(m.home_goals, m.away_goals)
        elif m.away == team:
            opp = m.home
            points += _result_points(m.away_goals, m.home_goals)
        else:
            continue
        opp_s = strength.get(opp, 0.0)
        opp_strengths.append(opp_s)
        # An average team (strength 0) faces this opponent.
        expected += avg_win_prob(-opp_s)
    n = len(opp_strengths)
    return ScheduleSummary(
        team=team,
        matches=n,
        mean_opponent_strength=sum(opp_strengths) / n if n else 0.0,
        points=points,
        expected_points_vs_schedule=expected,
    )
