"""Counterfactual scenarios, clearly labelled as model what-ifs.

A counterfactual asks: under the model, what would the xG of this shot have been if
it were taken from a different location or body part? It recomputes the model
output under the changed input. It never claims the player would actually have
scored; it is a statement about the model, which the label makes explicit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from touchline.features.shots import ShotFeatureRow


@dataclass(frozen=True)
class CounterfactualScenario:
    description: str
    # a transform applied to a feature row to produce the counterfactual row
    transform: Callable[[ShotFeatureRow], ShotFeatureRow]
    is_model_scenario: bool = True  # always true; counterfactuals are model what-ifs


@dataclass(frozen=True)
class CounterfactualResult:
    description: str
    baseline_xg: float
    scenario_xg: float
    is_model_scenario: bool

    @property
    def delta(self) -> float:
        return self.scenario_xg - self.baseline_xg

    def caption(self) -> str:
        return (
            f"model scenario: {self.description} changes xG by {self.delta:+.3f} "
            "(not an observed outcome)"
        )


def apply_scenario(
    row: ShotFeatureRow,
    scenario: CounterfactualScenario,
    predict: Callable[[list[float]], float],
) -> CounterfactualResult:
    baseline = predict(row.dense_vector())
    changed = scenario.transform(row)
    scenario_xg = predict(changed.dense_vector())
    return CounterfactualResult(
        description=scenario.description,
        baseline_xg=baseline,
        scenario_xg=scenario_xg,
        is_model_scenario=True,
    )
