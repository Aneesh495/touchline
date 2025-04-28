"""Analysis utilities for the interface: counterfactuals and comparisons.

These are explicitly model scenarios, not causal claims. A counterfactual recomputes
an outcome under a changed input and is labelled as a what-if. Comparisons apply
denominator filters, role matching, and sample-size disclosure so a two-match player
is not placed above a season-long one without that being visible.
"""

from touchline.analysis.compare import ComparisonRow, compare_players
from touchline.analysis.counterfactual import CounterfactualScenario, apply_scenario

__all__ = [
    "CounterfactualScenario",
    "apply_scenario",
    "ComparisonRow",
    "compare_players",
]
