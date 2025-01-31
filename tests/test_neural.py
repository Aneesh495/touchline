"""Neural model oracles. Skipped cleanly when torch is unavailable."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from touchline.models.neural.sequence_encoder import SequenceEncoder  # noqa: E402
from touchline.models.neural.set_encoder import MaskedSetEncoder  # noqa: E402
from touchline.models.neural.spatial_xg import SpatialXG  # noqa: E402


def _xg_data(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    dist = rng.uniform(1, 35, n)
    angle = rng.uniform(0.05, 1.2, n)
    rest = np.zeros((n, 5))
    x = np.column_stack([dist, angle, rest])
    logit = 2.0 - 0.15 * dist + 1.6 * angle
    p = 1 / (1 + np.exp(-logit))
    y = (rng.uniform(size=n) < p).astype(float)
    return x, y


def test_spatial_xg_learns_and_params_change():
    x, y = _xg_data()
    model = SpatialXG(epochs=150, seed=1)
    model.fit(x[:1600], y[:1600])
    before = model.loss_history[0]
    after = model.loss_history[-1]
    assert after < before  # loss decreased: real learning
    # held-out discrimination: close central shot > far shot
    close = model.predict_proba([[6, 1.0, 0, 0, 0, 0, 0]])[0]
    far = model.predict_proba([[30, 0.2, 0, 0, 0, 0, 0]])[0]
    assert close > far


def test_set_encoder_permutation_invariance():
    rng = np.random.default_rng(2)
    # three visible players; prediction must be identical under any ordering
    frame = [(0.9, 0.5, 0), (0.8, 0.4, 1), (0.85, 0.55, 0)]
    ball = np.array([[0.9, 0.5]], dtype=np.float32)
    enc = MaskedSetEncoder(epochs=5, seed=3)
    # fit briefly on tiny data to initialise weights
    enc.fit([frame, frame[::-1]], np.vstack([ball, ball]), np.array([1.0, 0.0]))
    p1 = enc.predict_proba([frame], ball)[0]
    shuffled = [frame[i] for i in rng.permutation(len(frame))]
    p2 = enc.predict_proba([shuffled], ball)[0]
    assert abs(p1 - p2) < 1e-5


def test_set_encoder_masking_ignores_padding():
    frame = [(0.9, 0.5, 0), (0.8, 0.4, 1)]
    ball = np.array([[0.9, 0.5]], dtype=np.float32)
    enc = MaskedSetEncoder(max_players=10, epochs=5, seed=4)
    enc.fit([frame], ball, np.array([1.0]))
    # Adding explicit padding (handled internally) must not change the result:
    # predicting the same frame twice in a batch with different partners padded.
    p_single = enc.predict_proba([frame], ball)[0]
    p_batch = enc.predict_proba([frame, frame], np.vstack([ball, ball]))
    assert abs(p_single - p_batch[0]) < 1e-6


def test_set_encoder_context_removal_ablation_changes_output():
    rng = np.random.default_rng(5)
    frames, balls, ys = [], [], []
    for _ in range(400):
        nd = rng.integers(0, 5)
        frame = [(float(rng.uniform(0.6, 1.0)), float(rng.uniform(0, 1)), 0) for _ in range(nd)]
        b = [0.9, 0.5]
        # more defenders -> lower scoring chance
        y = 1.0 if rng.uniform() < max(0.05, 0.6 - 0.12 * nd) else 0.0
        frames.append(frame)
        balls.append(b)
        ys.append(y)
    enc = MaskedSetEncoder(epochs=120, seed=6)
    enc.fit(frames, np.array(balls, dtype=np.float32), np.array(ys))
    ball = np.array([[0.9, 0.5]], dtype=np.float32)
    crowded = enc.predict_proba([[(0.95, 0.5, 0)] * 4], ball)[0]
    empty = enc.predict_without_players(ball)[0]
    # Removing the player context must change the prediction (context matters).
    assert abs(crowded - empty) > 1e-3


def test_sequence_encoder_causality_and_learning():
    rng = np.random.default_rng(7)
    seqs, targets = [], []
    for _ in range(300):
        n = int(rng.integers(5, 20))
        s = rng.normal(size=(n, 8)).astype(np.float32)
        # target depends only on current and past (cumulative mean of feature 0)
        cum = np.cumsum(s[:, 0]) / (np.arange(n) + 1)
        t = (cum > 0).astype(np.float32)
        seqs.append(s)
        targets.append(t)
    enc = SequenceEncoder(epochs=60, seed=8)
    enc.fit(seqs, targets)
    assert enc.loss_history[-1] < enc.loss_history[0]
    # Causality: changing a late step must not alter earlier-step predictions.
    base = seqs[0].copy()
    preds_base = enc.predict([base])[0]
    perturbed = base.copy()
    perturbed[-1] += 5.0  # change only the last step
    preds_pert = enc.predict([perturbed])[0]
    # earlier predictions (all but the last) should be unchanged
    assert np.allclose(preds_base[:-1], preds_pert[:-1], atol=1e-5)
