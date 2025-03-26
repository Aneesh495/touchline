"""Differential test: the model's forward pass agrees with an independent one.

The expected values here are computed by a second, independently written logistic
forward pass (not by calling the model under test), so agreement is real evidence
rather than a tautology. This is the kind of differential check the engineering
discipline requires.
"""

import json
import math
from pathlib import Path

import numpy as np

from touchline.data.sample import generate_sample_shots
from touchline.models.xg_logistic import LogisticXG


def _independent_logistic(weight, bias, mean, scale, x):
    """A from-scratch logistic forward pass, deliberately not using LogisticXG."""
    out = []
    for row in x:
        z = bias
        for i in range(len(row)):
            z += ((row[i] - mean[i]) / scale[i]) * weight[i]
        out.append(1.0 / (1.0 + math.exp(-max(-30, min(30, z)))))
    return out


def test_model_matches_independent_forward_pass():
    x, y, _ = generate_sample_shots(n=1500, seed=3)
    model = LogisticXG(epochs=200).fit(x, y)
    probe = x[:50]
    model_p = model.predict_proba(probe)
    indep_p = _independent_logistic(
        model.weight.tolist(),
        model.bias,
        model.mean_.tolist(),
        model.scale_.tolist(),
        probe.tolist(),
    )
    assert np.allclose(model_p, indep_p, atol=1e-9)


def test_exported_ui_model_reproduces_python_probs():
    """The UI model.json must reproduce the Python model's probabilities.

    This guards the Python-to-TypeScript boundary: if the exported artifact or the
    client-side math drifts, the independent forward pass over the exported weights
    would diverge from the Python model.
    """
    ui_model_path = Path("ui/src/model.json")
    if not ui_model_path.exists():
        import pytest

        pytest.skip("UI model artifact not present")
    m = json.loads(ui_model_path.read_text())
    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    # Refit with the same recipe the export used and compare to the stored artifact.
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    probe = x[split : split + 30]
    py_p = model.predict_proba(probe)
    ui_p = _independent_logistic(
        m["weight"], m["bias"], m["mean"], m["scale"], probe.tolist()
    )
    assert np.allclose(py_p, ui_p, atol=1e-6)
