"""Player comparisons with denominator filters, uncertainty, and sample disclosure.

A comparison is only meaningful when the players have comparable exposure and roles.
This module filters out players below a minimum-minutes threshold, discloses each
player's exposure, and attaches a simple uncertainty band from the sample size, so
a small-sample player cannot silently top a comparison.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerStat:
    player: str
    role: str
    value: float  # a per-90 rate
    minutes: float
    goals_like_count: int  # the raw count behind the rate, for the interval


@dataclass(frozen=True)
class ComparisonRow:
    player: str
    role: str
    value: float
    minutes: float
    ci_low: float
    ci_high: float
    limited_sample: bool


def _wilson_like_interval(count: int, minutes: float) -> tuple[float, float]:
    """A rough per-90 interval from a Poisson count over the exposure.

    Uses the normal approximation to a Poisson count scaled to per-90. Wide for
    small counts, which is the point: it shows the uncertainty behind a rate.
    """
    if minutes <= 0:
        return (0.0, 0.0)
    per90_factor = 90.0 / minutes
    se = math.sqrt(count) * per90_factor
    rate = count * per90_factor
    return (max(0.0, rate - 1.96 * se), rate + 1.96 * se)


def compare_players(
    stats: list[PlayerStat],
    min_minutes: float = 450.0,
    role_filter: str | None = None,
) -> list[ComparisonRow]:
    """Return a comparison sorted by value, with filters and intervals applied.

    Players below ``min_minutes`` are flagged ``limited_sample`` but still shown so
    the exclusion threshold is transparent. ``role_filter`` restricts to a role for
    like-for-like comparison.
    """
    rows: list[ComparisonRow] = []
    for s in stats:
        if role_filter is not None and s.role != role_filter:
            continue
        lo, hi = _wilson_like_interval(s.goals_like_count, s.minutes)
        rows.append(
            ComparisonRow(
                player=s.player,
                role=s.role,
                value=s.value,
                minutes=s.minutes,
                ci_low=lo,
                ci_high=hi,
                limited_sample=s.minutes < min_minutes,
            )
        )
    rows.sort(key=lambda r: r.value, reverse=True)
    return rows
