"""The evidence verifier driver.

Given an evidence directory, the verifier loads the raw records and the claimed
results, recomputes the decisive quantities independently, runs the semantic
checks, and performs a bounded model replay: it reloads the saved xG model and
re-scores a frozen probe set, confirming the reproduced metric matches the claimed
one within tolerance. It never trusts a stored pass flag and never retrains.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from touchline.models.calibration import log_loss
from touchline.verify.checks import (
    check_goal_labels_consistent,
    check_no_future_features,
    check_pitch_direction,
    check_qualification_possible,
)


def verify_evidence(evidence_path: str | None, verbose: bool = True) -> bool:
    """Verify an evidence bundle. Returns True only if every check passes."""
    if evidence_path is None:
        if verbose:
            print("verify: no --evidence path given")
        return False
    root = Path(evidence_path)
    if not root.exists():
        if verbose:
            print(f"verify: evidence path {root} does not exist")
        return False

    reasons: list[str] = []

    manifest = _load_json(root / "MANIFEST.json")
    if manifest is None:
        return _fail(["MANIFEST.json missing or invalid"], verbose)

    # 1. Semantic checks recomputed from raw records.
    feats = _load_json(root / "feature_records.json") or []
    shots = _load_json(root / "shot_records.json") or []
    sims = _load_json(root / "sim_records.json") or []
    reasons += check_no_future_features(feats)
    reasons += check_pitch_direction(shots)
    reasons += check_goal_labels_consistent(shots)
    reasons += check_qualification_possible(sims)

    # 2. Bounded replay: reload the saved xG model weights and re-score the probe.
    replay = _replay_xg(root)
    if replay is not None:
        reproduced, claimed = replay
        if abs(reproduced - claimed) > 1e-6:
            reasons.append(
                f"replay log loss {reproduced:.6f} != claimed {claimed:.6f}"
            )

    if reasons:
        return _fail(reasons, verbose)
    if verbose:
        print(f"verify: all checks passed for {root}")
    return True


def _replay_xg(root: Path):
    """Recompute the xG held-out log loss from saved weights and a frozen probe.

    The saved model is a plain logistic weight vector and bias plus the feature
    standardisation, stored as JSON. The verifier reimplements the forward pass
    rather than importing the training model, so a broken training routine cannot
    hide behind a shared code path.
    """
    probe = _load_json(root / "xg_probe.json")
    model = _load_json(root / "xg_model.json")
    claimed = _load_json(root / "xg_claimed.json")
    if probe is None or model is None or claimed is None:
        return None
    x = np.array(probe["x"], dtype=float)
    y = np.array(probe["y"], dtype=float)
    w = np.array(model["weight"], dtype=float)
    b = float(model["bias"])
    mean = np.array(model["mean"], dtype=float)
    scale = np.array(model["scale"], dtype=float)
    xs = (x - mean) / scale
    z = xs @ w + b
    p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
    reproduced = log_loss(y, p)
    return reproduced, float(claimed["xg_log_loss"])


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _fail(reasons: list[str], verbose: bool) -> bool:
    if verbose:
        print("verify: FAILED")
        for r in reasons:
            print(f"  - {r}")
    return False
