"""Pre-match team-strength features built chronologically.

For each match in date order we record the two teams' Elo ratings as they stand
*before* the match, then update the ratings with the result. The feature attached
to a match therefore only reflects earlier matches, which is exactly the
knowledge-time contract: a pre-match rating is knowable at kickoff.

The output rows carry the match date and group so they can be fed straight into
the chronological splitter with group-integrity preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from touchline.models.elo import EloModel


@dataclass(frozen=True)
class MatchRow:
    home: str
    away: str
    home_goals: int
    away_goals: int
    when: date
    competition: str
    season: str

    @property
    def group(self) -> str:
        return f"{self.competition}|{self.season}"

    @property
    def result(self) -> str:
        if self.home_goals > self.away_goals:
            return "H"
        if self.home_goals < self.away_goals:
            return "A"
        return "D"


@dataclass(frozen=True)
class StrengthFeatureRow:
    home: str
    away: str
    home_elo_pre: float
    away_elo_pre: float
    elo_diff: float
    home_prob: float
    draw_prob: float
    away_prob: float
    when: date
    group: str
    competition: str
    result: str  # label


def build_elo_features(
    matches: list[MatchRow], elo: EloModel | None = None
) -> list[StrengthFeatureRow]:
    """Walk matches in date order, emitting pre-match Elo features then updating.

    The same :class:`EloModel` instance accumulates ratings across the sequence, so
    row i sees only the effect of matches 0..i-1. Matches must be passed in
    chronological order; ties on date keep their given order.
    """
    elo = elo or EloModel()
    ordered = sorted(matches, key=lambda m: m.when)
    rows: list[StrengthFeatureRow] = []
    for m in ordered:
        home_pre = elo.rating(m.home)
        away_pre = elo.rating(m.away)
        ph, pd, pa = elo.predict_result_probs(m.home, m.away)
        rows.append(
            StrengthFeatureRow(
                home=m.home,
                away=m.away,
                home_elo_pre=home_pre,
                away_elo_pre=away_pre,
                elo_diff=home_pre - away_pre,
                home_prob=ph,
                draw_prob=pd,
                away_prob=pa,
                when=m.when,
                group=m.group,
                competition=m.competition,
                result=m.result,
            )
        )
        elo.update(m.home, m.away, m.home_goals, m.away_goals)
    return rows
