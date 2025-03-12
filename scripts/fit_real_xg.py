"""Fit the logistic xG model on real cached StatsBomb shots (manual check script)."""

from pathlib import Path

import numpy as np

from touchline.models.calibration import brier_score, log_loss
from touchline.models.xg_logistic import LogisticXG
from touchline.pipeline.statsbomb_pipeline import build_from_cache


def main() -> None:
    res = build_from_cache(
        Path("data/raw/cache"), 11, 90, "LALIGA", "2020-2021", max_matches=5
    )
    print("coverage", res.coverage.report())
    print("n_real_shots", res.n_shots)
    x, y = res.features, res.labels
    split = int(0.7 * len(y))
    m = LogisticXG(epochs=400).fit(x[:split], y[:split])
    p = m.predict_proba(x[split:])
    base = np.full(len(y) - split, y[:split].mean())
    print("real xG log loss", round(log_loss(y[split:], p), 4),
          "base", round(log_loss(y[split:], base), 4))
    print("real xG brier", round(brier_score(y[split:], p), 4))
    print("mean predicted xG", round(float(p.mean()), 4),
          "actual goal rate", round(float(y[split:].mean()), 4))


if __name__ == "__main__":
    main()
