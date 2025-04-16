"""Knockout bracket simulation.

A knockout is a single-elimination tree. Each tie is resolved by a win-probability
model (for a single match) or by the two-legged tie rules (for UCL knockouts). The
simulator draws many brackets and reports each team's probability of reaching each
round and of winning, with Monte Carlo error. A small bracket can be enumerated
exactly as a check.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

# A win-probability function: P(team_a beats team_b) in a single tie.
WinProb = Callable[[str, str], float]


@dataclass
class KnockoutResult:
    teams: list[str]
    n_sims: int
    # reached_round[team][r] = count of sims team reached round r (0 = first round)
    reached: dict[str, np.ndarray]
    titles: dict[str, int]

    def title_prob(self, team: str) -> float:
        return self.titles.get(team, 0) / self.n_sims

    def reach_prob(self, team: str, round_index: int) -> float:
        return float(self.reached[team][round_index] / self.n_sims)

    def monte_carlo_se(self, p: float) -> float:
        import math

        return math.sqrt(max(p * (1 - p), 0.0) / self.n_sims)


def simulate_knockout(
    bracket: list[str], win_prob: WinProb, n_sims: int = 10000, seed: int = 0
) -> KnockoutResult:
    """Simulate a single-elimination bracket.

    ``bracket`` lists the 2^k teams in seeding order (adjacent pairs meet first).
    ``win_prob(a, b)`` gives the probability a beats b in their tie.
    """
    n = len(bracket)
    if n & (n - 1) != 0:
        raise ValueError("bracket size must be a power of two")
    rounds = n.bit_length() - 1
    rng = np.random.default_rng(seed)
    reached = {t: np.zeros(rounds + 1, dtype=np.int64) for t in bracket}
    titles: dict[str, int] = {t: 0 for t in bracket}

    for _ in range(n_sims):
        alive = list(bracket)
        for t in alive:
            reached[t][0] += 1
        r = 1
        while len(alive) > 1:
            nxt = []
            for i in range(0, len(alive), 2):
                a, b = alive[i], alive[i + 1]
                p = win_prob(a, b)
                winner = a if rng.random() < p else b
                nxt.append(winner)
                reached[winner][r] += 1
            alive = nxt
            r += 1
        titles[alive[0]] += 1
    return KnockoutResult(bracket, n_sims, reached, titles)


@dataclass
class ExactKnockout:
    """Exact enumeration of a small bracket for checking the sampler."""

    bracket: list[str]
    win_prob: WinProb

    def title_probabilities(self) -> dict[str, float]:
        return self._solve(self.bracket)

    def _solve(self, teams: list[str]) -> dict[str, float]:
        if len(teams) == 1:
            return {teams[0]: 1.0}
        # Probability each team wins its half, then combine across the final.
        half = len(teams) // 2
        left = self._solve(teams[:half])
        right = self._solve(teams[half:])
        out: dict[str, float] = {t: 0.0 for t in teams}
        for a, pa in left.items():
            for b, pb in right.items():
                pab = self.win_prob(a, b)
                out[a] += pa * pb * pab
                out[b] += pa * pb * (1 - pab)
        return out
