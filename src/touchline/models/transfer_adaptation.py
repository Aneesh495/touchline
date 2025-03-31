"""Transfer adaptation: output before and after a move, chronologically separated.

A common question is whether a player's output dips then recovers after a transfer
(an adaptation period). The honest way to study this is to compare pre-transfer and
post-transfer output with strict chronological separation: the pre-transfer window
uses only matches before the move, and the post-transfer window only matches after,
with the move's known date respected so no post-move information informs a
pre-move reading.

This is a predictive, not causal, instrument. A player's post-move dip confounds
with a change of league strength, role, and teammates, which is stated as a
limitation rather than resolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np


@dataclass(frozen=True)
class OutputPoint:
    when: date
    per90: float
    minutes: float


@dataclass(frozen=True)
class AdaptationSummary:
    pre_mean: float
    post_early_mean: float  # first window after the move
    post_late_mean: float  # later window after the move
    pre_exposure: float
    post_exposure: float

    @property
    def early_dip(self) -> float:
        """Change from pre-move to the early post-move window (negative = dip)."""
        return self.post_early_mean - self.pre_mean

    @property
    def recovery(self) -> float:
        """Change from the early to the later post-move window."""
        return self.post_late_mean - self.post_early_mean


def summarise_adaptation(
    points: list[OutputPoint],
    move_date: date,
    early_days: int = 120,
) -> AdaptationSummary:
    """Split output into pre-move, early post-move, and later post-move windows.

    Minutes-weight each window's mean so a handful of low-minute appearances does
    not dominate. Chronological separation is strict: a match exactly on the move
    date is treated as post-move.
    """
    pre = [p for p in points if p.when < move_date]
    post = [p for p in points if p.when >= move_date]
    early = [p for p in post if (p.when - move_date).days < early_days]
    late = [p for p in post if (p.when - move_date).days >= early_days]

    def wmean(ps):
        if not ps:
            return 0.0
        w = np.array([p.minutes for p in ps], dtype=float)
        v = np.array([p.per90 for p in ps], dtype=float)
        return float((w * v).sum() / w.sum()) if w.sum() > 0 else 0.0

    return AdaptationSummary(
        pre_mean=wmean(pre),
        post_early_mean=wmean(early),
        post_late_mean=wmean(late),
        pre_exposure=float(sum(p.minutes for p in pre)),
        post_exposure=float(sum(p.minutes for p in post)),
    )
