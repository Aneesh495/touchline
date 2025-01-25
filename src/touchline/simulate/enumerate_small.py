"""Exact enumeration of small tournaments for checking the Monte Carlo sampler.

For a handful of remaining matches with a capped goal count, the full outcome
space is small enough to enumerate exactly. Summing the probability of every
outcome that leaves a team in a given position gives an exact answer that the
sampler must approach as the number of simulations grows. This is the independent
oracle required for the simulation gate.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import numpy as np

from touchline.simulate.rules import Fixture, LeagueRules, compute_table

# A scoreline probability function: P(home_goals=h, away_goals=a).
ScorelineProb = Callable[[str, str, int, int], float]


def enumerate_positions(
    teams: list[str],
    played: list[Fixture],
    remaining: list[tuple[str, str]],
    rules: LeagueRules,
    scoreline_prob: ScorelineProb,
    max_goals: int = 4,
) -> dict[str, np.ndarray]:
    """Return exact position-probability vectors for each team.

    Each remaining match ranges over scorelines 0..max_goals for each side. The
    scoreline probabilities need not sum to one over the truncated grid; they are
    renormalised per match so the enumeration is a proper distribution.
    """
    n = len(teams)
    result = {t: np.zeros(n) for t in teams}
    grids = []
    for h, a in remaining:
        probs = {}
        total = 0.0
        for hg in range(max_goals + 1):
            for ag in range(max_goals + 1):
                p = scoreline_prob(h, a, hg, ag)
                probs[(hg, ag)] = p
                total += p
        probs = {k: v / total for k, v in probs.items()}
        grids.append((h, a, probs))

    for combo in itertools.product(*[list(g[2].items()) for g in grids]):
        prob = 1.0
        fixtures = list(played)
        for (h, a, _), ((hg, ag), p) in zip(grids, combo, strict=True):
            prob *= p
            fixtures.append(Fixture(h, a, hg, ag))
        table = compute_table(teams, fixtures, rules)
        for pos, row in enumerate(table, start=1):
            result[row.team][pos - 1] += prob
    return result
