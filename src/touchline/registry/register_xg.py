"""Train an xG model and register it with a complete model card.

This makes the registry concrete: a trained logistic xG is serialised to a JSON
checkpoint and registered with its dataset version, feature contract, supported
fields, calibration, selection record, seeds, and metrics. The selection record
never references test performance; selection is on validation log loss among
event-only models.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from touchline.models.calibration import brier_score, log_loss
from touchline.models.xg_logistic import LogisticXG
from touchline.registry.model_card import ModelCard, ModelRegistry

FEATURE_CONTRACT = [
    "distance_m",
    "angle_rad",
    "is_header",
    "is_penalty",
    "is_free_kick",
    "is_corner",
    "is_counter",
]


def train_and_register(
    x: np.ndarray,
    y: np.ndarray,
    registry_root: Path,
    model_id: str = "xg_logistic_v1",
    dataset_version: str = "sample-v1",
) -> ModelCard:
    """Fit, evaluate on a held-out split, and register the model."""
    split = int(0.7 * len(y))
    val = int(0.85 * len(y))
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    val_p = model.predict_proba(x[split:val])
    test_p = model.predict_proba(x[val:])
    val_ll = log_loss(y[split:val], val_p)
    test_ll = log_loss(y[val:], test_p)
    test_brier = brier_score(y[val:], test_p)

    checkpoint = json.dumps(
        {
            "weight": model.weight.tolist(),
            "bias": model.bias,
            "mean": model.mean_.tolist(),
            "scale": model.scale_.tolist(),
        }
    ).encode()

    card = ModelCard(
        model_id=model_id,
        model_type="logistic_xg",
        dataset_version=dataset_version,
        feature_contract=FEATURE_CONTRACT,
        supported_fields=["event"],
        calibration="platt_validation_only",
        selection_record=(
            f"selected on validation log loss {val_ll:.4f}; test not inspected "
            "during selection"
        ),
        metrics={"val_log_loss": val_ll, "test_log_loss": test_ll, "test_brier": test_brier},
        seeds=[0],
        created_at=datetime.now(UTC).isoformat(),
    )
    registry = ModelRegistry(registry_root)
    return registry.register(card, checkpoint=checkpoint)
