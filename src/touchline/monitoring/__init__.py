"""Drift monitoring and historical backtesting.

Models trained on one period can degrade when the game or the data changes (a rule
change, a new provider revision, a format change). This layer monitors the
distribution of inputs and the model's calibration over time and backtests across
known disruptions, using only the data available as of each point so a later
revision is never silently used to judge an earlier prediction.
"""

from touchline.monitoring.drift import (
    DriftReport,
    calibration_drift,
    population_stability_index,
)

__all__ = ["DriftReport", "population_stability_index", "calibration_drift"]
