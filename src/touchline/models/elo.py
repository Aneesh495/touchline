"""Dynamic Elo ratings for football with home advantage and draws.

Elo is a simple, identifiable, online strength model. Each team carries a rating;
after a match the ratings move toward the observed result in proportion to the
surprise. Football needs two adaptations from chess Elo: a home-advantage offset
added to the home team's effective rating, and a three-outcome result mapped to a
score in [0, 1] (win 1, draw 0.5, loss 0).

The expected home score uses the logistic
    E_home = 1 / (1 + 10 ** (-(R_home + H - R_away) / 400))
and the update is R <- R + K * (S - E). Goal difference optionally scales K so a
heavier win moves ratings more, a common and well-documented refinement.

Ratings evolve chronologically, so a rating used to predict a match only reflects
matches played strictly earlier. That ordering is the caller's responsibility and
is enforced by the chronological evaluation harness.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class EloModel:
    k: float = 20.0
    home_advantage: float = 60.0
    base_rating: float = 1500.0
    use_goal_margin: bool = True
    ratings: dict[str, float] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.get(team, self.base_rating)

    def expected_home_score(self, home: str, away: str) -> float:
        diff = self.rating(home) + self.home_advantage - self.rating(away)
        return 1.0 / (1.0 + math.pow(10.0, -diff / 400.0))

    def predict_result_probs(self, home: str, away: str) -> tuple[float, float, float]:
        """Return (P(home win), P(draw), P(away win)).

        Elo yields an expected score, not a draw probability directly. We split
        the expected score into win/draw/loss with a draw model whose width grows
        when the teams are evenly matched. The draw share is a smooth function of
        the rating gap, calibrated to the roughly 25% league draw base rate at
        parity and shrinking as the gap widens.
        """
        e_home = self.expected_home_score(home, away)
        gap = abs(self.rating(home) + self.home_advantage - self.rating(away))
        draw = 0.28 * math.exp(-gap / 300.0)
        draw = min(max(draw, 0.05), 0.40)
        # The non-draw mass is split between home and away in proportion to the
        # expected score, so the three probabilities sum to one by construction.
        p_home = (1.0 - draw) * e_home
        p_away = (1.0 - draw) * (1.0 - e_home)
        return p_home, draw, p_away

    def update(self, home: str, away: str, home_goals: int, away_goals: int) -> None:
        e_home = self.expected_home_score(home, away)
        if home_goals > away_goals:
            s_home = 1.0
        elif home_goals < away_goals:
            s_home = 0.0
        else:
            s_home = 0.5
        k = self.k
        if self.use_goal_margin:
            margin = abs(home_goals - away_goals)
            if margin >= 2:
                k = self.k * (1.0 + math.log(margin))
        delta = k * (s_home - e_home)
        self.ratings[home] = self.rating(home) + delta
        self.ratings[away] = self.rating(away) - delta
