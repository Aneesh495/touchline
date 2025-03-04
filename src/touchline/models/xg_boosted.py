"""Gradient-boosted expected goals (the GBM comparison baseline).

This is the gradient-boosted comparison required alongside the logistic and neural
xG models. The project owns the target construction, the temporal protocol, and the
feature contract; the gradient-boosting estimator itself is provided by LightGBM,
which is permitted as a numerical primitive. Early stopping uses a validation set,
never the test set, and the model is skipped cleanly when LightGBM is unavailable.

Keeping all three xG models on the identical feature contract is what makes the H1
comparison fair: any difference is the model family, not the inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _require_lightgbm():
    try:
        import lightgbm as lgb

        return lgb
    except ImportError as exc:  # pragma: no cover - exercised only without lgbm
        raise ImportError(
            "The boosted xG model needs LightGBM. Install the optional extra: "
            "uv pip install -e '.[boost]'"
        ) from exc


@dataclass
class BoostedXG:
    num_leaves: int = 15
    learning_rate: float = 0.05
    n_estimators: int = 300
    min_child_samples: int = 40
    seed: int = 0
    _booster: object = field(default=None, init=False)
    best_iteration: int = field(default=0, init=False)

    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        sample_weight: np.ndarray | None = None,
    ) -> BoostedXG:
        lgb = _require_lightgbm()
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        train = lgb.Dataset(x, label=y, weight=sample_weight)
        params = {
            "objective": "binary",
            "metric": "binary_logloss",
            "num_leaves": self.num_leaves,
            "learning_rate": self.learning_rate,
            "min_child_samples": self.min_child_samples,
            "seed": self.seed,
            "verbose": -1,
        }
        callbacks = []
        valid_sets = [train]
        if x_val is not None and y_val is not None:
            valid_sets.append(lgb.Dataset(np.asarray(x_val, dtype=float), label=np.asarray(y_val, dtype=float)))
            callbacks.append(lgb.early_stopping(30, verbose=False))
        self._booster = lgb.train(
            params,
            train,
            num_boost_round=self.n_estimators,
            valid_sets=valid_sets,
            callbacks=callbacks,
        )
        self.best_iteration = getattr(self._booster, "best_iteration", 0) or self.n_estimators
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self._booster is None:
            raise RuntimeError("model not fitted")
        return np.asarray(
            self._booster.predict(np.asarray(x, dtype=float)), dtype=float
        )

    def feature_importance(self) -> np.ndarray:
        if self._booster is None:
            raise RuntimeError("model not fitted")
        return np.asarray(self._booster.feature_importance(importance_type="gain"))
