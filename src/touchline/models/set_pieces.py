"""Set-piece sequence models for corners and free kicks.

Set pieces are rare-event sequences: a corner or free kick starts a short possession
that occasionally yields a shot and rarely a goal. Conversion is estimated with
partial pooling over teams because per-team goal counts are tiny, and over a
declared possession/time horizon so the denominator is explicit. Direct and
second-phase outcomes are separated: a free kick shot straight at goal is a
different process from a free kick that is crossed and headed in.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from touchline.models.hierarchical import HierarchicalRateModel


@dataclass(frozen=True)
class SetPieceOutcome:
    team: str
    attempts: int  # corners or free kicks of the relevant type
    shots_within_horizon: int
    goals_within_horizon: int
    direct_goals: int  # goals scored directly from the delivery


@dataclass
class SetPieceConversionModel:
    """Shrunk conversion rates per team for a set-piece type."""

    rate_model: HierarchicalRateModel = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.rate_model is None:
            self.rate_model = HierarchicalRateModel()

    def fit_conversion(self, outcomes: list[SetPieceOutcome]):
        """Shrink goals-per-attempt toward the population rate.

        Returns shrunk estimates with exposure (attempts) disclosed, so a team with
        three corners does not top a leaderboard on a single lucky goal.
        """
        keys = [o.team for o in outcomes]
        goals = np.array([o.goals_within_horizon for o in outcomes], dtype=float)
        attempts = np.array([o.attempts for o in outcomes], dtype=float)
        return self.rate_model.shrink(keys, goals, attempts)

    @staticmethod
    def direct_fraction(outcomes: list[SetPieceOutcome]) -> float:
        """Fraction of set-piece goals scored directly from the delivery.

        Separates direct from second-phase outcomes at the population level. Zero
        when there are no goals (reported, not a division error).
        """
        total_goals = sum(o.goals_within_horizon for o in outcomes)
        direct = sum(o.direct_goals for o in outcomes)
        return direct / total_goals if total_goals else 0.0
