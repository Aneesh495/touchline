"""Rolling-origin evaluation for the team-strength forecast.

For a longitudinal forecasting family, the right protocol is rolling origins: train
on everything before a cut, test on the next window, advance the cut, repeat. Each
fold trains only on the past, so the evaluation is an honest out-of-time forecast
rather than a random split. This driver runs the Elo result forecaster across
rolling cuts on a dated match list and reports per-fold proper scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from touchline.features.splits import DatedItem, rolling_origin_splits
from touchline.features.team_strength import MatchRow, build_elo_features
from touchline.models.calibration import log_loss


@dataclass
class FoldResult:
    cut: date
    n_train: int
    n_test: int
    log_loss: float
    baseline_log_loss: float  # constant home/draw/away base rates


def rolling_elo_forecast(matches: list[MatchRow], cuts: list[date]) -> list[FoldResult]:
    """Evaluate the Elo result forecaster across rolling chronological origins.

    For each fold, the Elo ratings are built from the training matches only, then
    used to predict the test matches' result probabilities. The proper score is the
    multiclass log loss against the three-way outcome, compared to a base-rate
    predictor fit on the training outcomes.
    """
    items = [
        DatedItem(m, m.when, m.group, m.competition) for m in matches
    ]
    folds = rolling_origin_splits(items, cuts)
    results: list[FoldResult] = []
    for split in folds:
        if not split.test or not split.train:
            continue
        # Build Elo from training matches in date order.
        feats = build_elo_features(list(split.train))
        elo = _elo_from_features(split.train)
        # Base rates from training outcomes.
        base = _base_rates([m.result for m in split.train])
        ll = _multiclass_ll(elo, split.test)
        bll = _multiclass_ll_const(base, split.test)
        results.append(
            FoldResult(
                cut=split.cut,  # type: ignore[arg-type]
                n_train=len(split.train),
                n_test=len(split.test),
                log_loss=ll,
                baseline_log_loss=bll,
            )
        )
        _ = feats
    return results


def _elo_from_features(train: list[MatchRow]):
    from touchline.models.elo import EloModel

    elo = EloModel()
    for m in sorted(train, key=lambda r: r.when):
        elo.update(m.home, m.away, m.home_goals, m.away_goals)
    return elo


def _base_rates(results: list[str]) -> tuple[float, float, float]:
    n = len(results) or 1
    h = results.count("H") / n
    d = results.count("D") / n
    a = results.count("A") / n
    return h, d, a


def _multiclass_ll(elo, test: list[MatchRow]) -> float:
    eps = 1e-12
    total = 0.0
    for m in test:
        ph, pd, pa = elo.predict_result_probs(m.home, m.away)
        p = {"H": ph, "D": pd, "A": pa}[m.result]
        total += -np.log(max(p, eps))
    return total / max(len(test), 1)


def _multiclass_ll_const(base: tuple[float, float, float], test: list[MatchRow]) -> float:
    eps = 1e-12
    ph, pd, pa = base
    probs = {"H": ph, "D": pd, "A": pa}
    total = 0.0
    for m in test:
        total += -np.log(max(probs[m.result], eps))
    return total / max(len(test), 1)


_ = log_loss  # referenced for the proper-score family
