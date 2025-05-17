"""Contract-horizon associations with censoring and competing events.

Hypothesis H12 asks whether a shortening contract horizon is associated with a
transfer. This is a survival-style question: a player is observed from a point in
time until they either transfer (the event), sign an extension (a competing event
that resets the horizon), or the observation window ends (censoring). The honest
treatment keeps censored and competing-event cases distinct and never claims a
causal effect of the horizon on the club's decision, which depends on private
negotiations.

This module builds the survival records and computes a simple Kaplan-Meier style
survival curve for "time to transfer" within horizon bands, so the association can
be read without overclaiming.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    TRANSFER = "transfer"  # the event of interest
    EXTENSION = "extension"  # competing event: horizon reset
    CENSORED = "censored"  # observation ended before any event


@dataclass(frozen=True)
class SurvivalRecord:
    player: str
    months_observed: float
    outcome: Outcome
    horizon_months_at_start: float  # contract months remaining at observation start


def kaplan_meier(records: list[SurvivalRecord], horizon_band: tuple[float, float]):
    """Kaplan-Meier survival (not-yet-transferred) for a horizon band.

    Only records whose starting horizon falls in the band are included. Extensions
    and censoring are treated as censored for the transfer event (they remove the
    player from the at-risk set without counting as a transfer). Returns a list of
    (time, survival) points.
    """
    lo, hi = horizon_band
    cohort = [r for r in records if lo <= r.horizon_months_at_start < hi]
    # order by observed time
    cohort.sort(key=lambda r: r.months_observed)
    n_at_risk = len(cohort)
    survival = 1.0
    curve: list[tuple[float, float]] = [(0.0, 1.0)]
    for r in cohort:
        if n_at_risk == 0:
            break
        if r.outcome is Outcome.TRANSFER:
            survival *= 1.0 - 1.0 / n_at_risk
            curve.append((r.months_observed, survival))
        # transfers and censored/extension events both leave the at-risk set
        n_at_risk -= 1
    return curve


def median_survival(curve: list[tuple[float, float]]) -> float | None:
    """The time at which survival first drops to or below 0.5, or None."""
    for t, s in curve:
        if s <= 0.5:
            return t
    return None
