"""Finishing persistence: does goals-minus-xG repeat across split halves?

Hypothesis H2 asks whether finishing skill (scoring more than your xG) is a stable
trait or noise. The operational test is a split-half correlation: split each
player's shots into two halves, compute goals minus xG per 100 shots in each half,
and correlate the halves across players. A positive correlation with a confidence
interval excluding zero is evidence of persistence; near zero is evidence it is
mostly noise.

A minimum shot count per half is required so the halves are not dominated by tiny
samples, and that threshold is disclosed with the result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PlayerShots:
    player: str
    goals: list[int]  # 0/1 per shot in chronological order
    xg: list[float]  # model xG per shot, aligned with goals


@dataclass(frozen=True)
class PersistenceResult:
    correlation: float
    n_players: int
    min_shots_per_half: int
    ci_low: float
    ci_high: float

    @property
    def persistent(self) -> bool:
        """Persistent when the CI excludes zero in the positive direction."""
        return self.ci_low > 0.0


def _overperformance(goals: list[int], xg: list[float]) -> float:
    shots = len(goals)
    if shots == 0:
        return 0.0
    return (sum(goals) - sum(xg)) / shots * 100.0  # per 100 shots


def split_half_persistence(
    players: list[PlayerShots], min_shots_per_half: int = 30, n_boot: int = 1000, seed: int = 0
) -> PersistenceResult:
    """Correlate first-half and second-half finishing over-performance across players."""
    first, second = [], []
    for p in players:
        n = len(p.goals)
        half = n // 2
        if half < min_shots_per_half:
            continue
        first.append(_overperformance(p.goals[:half], p.xg[:half]))
        second.append(_overperformance(p.goals[half:], p.xg[half:]))
    first_arr = np.array(first)
    second_arr = np.array(second)
    if len(first_arr) < 3:
        return PersistenceResult(float("nan"), len(first_arr), min_shots_per_half, float("nan"), float("nan"))
    corr = float(np.corrcoef(first_arr, second_arr)[0, 1])
    # bootstrap CI over players
    rng = np.random.default_rng(seed)
    boots = []
    m = len(first_arr)
    for _ in range(n_boot):
        idx = rng.integers(0, m, m)
        if np.std(first_arr[idx]) < 1e-9 or np.std(second_arr[idx]) < 1e-9:
            continue
        boots.append(np.corrcoef(first_arr[idx], second_arr[idx])[0, 1])
    lo, hi = (
        (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))
        if boots
        else (float("nan"), float("nan"))
    )
    return PersistenceResult(corr, m, min_shots_per_half, lo, hi)
