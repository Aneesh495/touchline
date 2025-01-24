"""Original models with documented targets.

Each model owns its target definition, its fitting procedure, and its evaluation
contract. Libraries are used for numerical primitives (numpy, scipy) and, where
noted, for a boosting baseline; the target construction, temporal protocol, and
interpretation are implemented here.

Models in this package:

* :mod:`elo` dynamic team strength with home advantage.
* :mod:`dixon_coles` a Poisson/Dixon-Coles score model with low-score correction.
* :mod:`xg_logistic` a logistic expected-goals model fit by gradient descent.
* :mod:`expected_threat` a grid value-iteration solve with absorbing outcomes.
* :mod:`action_value` possession action value over a declared horizon.
* :mod:`calibration` validation-only probability calibration and reliability.
"""

from touchline.models.calibration import (
    PlattCalibrator,
    brier_score,
    log_loss,
    reliability_table,
)
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.elo import EloModel
from touchline.models.xg_logistic import LogisticXG

__all__ = [
    "EloModel",
    "DixonColesModel",
    "LogisticXG",
    "PlattCalibrator",
    "brier_score",
    "log_loss",
    "reliability_table",
]
