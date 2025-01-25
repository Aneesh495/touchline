"""Deterministic synthetic sample generators, clearly labelled as synthetic.

These produce a small league of fixtures and a set of shots with a known
data-generating process. Because the truth is known, they double as regression
fixtures: the demo and tests can check that fitted models recover the planted
structure. They are not real matches and are never counted toward any real-data
coverage gate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SampleLeague:
    """A generated single round-robin (home and away) league season."""

    teams: list[str]
    home: list[str]
    away: list[str]
    home_goals: list[int]
    away_goals: list[int]
    true_strength: dict[str, float]
    match_date_index: list[int]  # chronological order index per fixture

    @property
    def n_matches(self) -> int:
        return len(self.home)


def generate_sample_league(
    n_teams: int = 10, seed: int = 7, home_adv: float = 0.30
) -> SampleLeague:
    """Generate a double round-robin from latent team strengths.

    Goals are Poisson with log-mean built from attacking strength minus opponent
    strength and a home boost. Fixtures are ordered so that each matchday precedes
    the next, giving the chronological structure the evaluation harness needs.
    """
    rng = np.random.default_rng(seed)
    teams = [f"Club {chr(ord('A') + i)}" for i in range(n_teams)]
    strength = {t: float(rng.normal(0.0, 0.35)) for t in teams}
    home, away, hg, ag, order = [], [], [], [], []
    matchday = 0
    fixtures = [(h, a) for h in teams for a in teams if h != a]
    rng.shuffle(fixtures)
    for i, (h, a) in enumerate(fixtures):
        lam = np.exp(0.1 + home_adv + strength[h] - strength[a])
        mu = np.exp(0.1 + strength[a] - strength[h])
        home.append(h)
        away.append(a)
        hg.append(int(rng.poisson(lam)))
        ag.append(int(rng.poisson(mu)))
        order.append(i // (n_teams // 2) if n_teams >= 2 else 0)
        matchday = i
    _ = matchday
    return SampleLeague(teams, home, away, hg, ag, strength, order)


def generate_sample_shots(
    n: int = 3000, seed: int = 11, with_spatial_fraction: float = 0.2
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate shot feature rows with a known goal model.

    Returns ``(features, labels, has_spatial)``. The true goal log-odds decrease
    with distance and increase with shot angle, with a penalty bump. A fraction of
    shots carry a spatial defender count that modestly lowers conversion, used to
    exercise the spatial-aware path.
    """
    rng = np.random.default_rng(seed)
    dist = rng.uniform(1.0, 35.0, n)
    angle = rng.uniform(0.03, 1.3, n)
    is_header = (rng.uniform(size=n) < 0.15).astype(float)
    is_pen = (rng.uniform(size=n) < 0.04).astype(float)
    is_fk = (rng.uniform(size=n) < 0.05).astype(float)
    is_corner = (rng.uniform(size=n) < 0.08).astype(float)
    is_counter = (rng.uniform(size=n) < 0.1).astype(float)
    has_spatial = (rng.uniform(size=n) < with_spatial_fraction).astype(float)
    defenders = np.where(has_spatial > 0, rng.integers(0, 5, n), 0)

    logit = (
        1.5
        - 0.16 * dist
        + 1.6 * angle
        - 0.5 * is_header
        + 3.0 * is_pen
        - 0.3 * is_counter * 0
        - 0.25 * defenders
    )
    p = 1.0 / (1.0 + np.exp(-logit))
    y = (rng.uniform(size=n) < p).astype(float)
    x = np.column_stack(
        [dist, angle, is_header, is_pen, is_fk, is_corner, is_counter]
    )
    return x, y, has_spatial
