"""Goalkeeping: shot-stopping only where placement inputs genuinely exist.

Goals prevented is the difference between the expected goals a keeper faced
(post-shot, using shot placement) and the goals actually conceded. It requires a
post-shot model whose inputs include where the shot was placed in the goal. Without
those inputs the measure is not computed; this module refuses to fabricate placement
from the final score and returns an explicit unavailable status instead.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShotFaced:
    on_target: bool
    goal: bool
    placement_known: bool
    post_shot_xg: float | None  # expected goal probability given placement, if known


@dataclass(frozen=True)
class GoalkeepingReport:
    shots_on_target_faced: int
    goals_conceded: int
    goals_prevented: float | None  # None when placement inputs are missing
    eligible: bool
    reason: str = ""


def goalkeeping_report(shots: list[ShotFaced]) -> GoalkeepingReport:
    """Compute goals prevented only when every on-target shot has placement.

    If any on-target shot lacks a known placement (and therefore a post-shot xG),
    goals prevented is not computed and the report says why. Save percentage is
    always available because it needs only the on-target and goal counts.
    """
    on_target = [s for s in shots if s.on_target]
    goals = sum(1 for s in on_target if s.goal)
    missing = [s for s in on_target if not s.placement_known or s.post_shot_xg is None]
    if missing:
        return GoalkeepingReport(
            shots_on_target_faced=len(on_target),
            goals_conceded=goals,
            goals_prevented=None,
            eligible=False,
            reason=f"{len(missing)} on-target shots lack placement; "
            "goals prevented not computed",
        )
    expected_conceded = sum(s.post_shot_xg for s in on_target)  # type: ignore[misc]
    return GoalkeepingReport(
        shots_on_target_faced=len(on_target),
        goals_conceded=goals,
        goals_prevented=expected_conceded - goals,
        eligible=True,
    )


def save_percentage(shots: list[ShotFaced]) -> float:
    on_target = [s for s in shots if s.on_target]
    if not on_target:
        return 0.0
    saved = sum(1 for s in on_target if not s.goal)
    return saved / len(on_target)
