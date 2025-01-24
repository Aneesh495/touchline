"""Logistic expected-goals model.

Expected goals is the probability that a shot becomes a goal, modelled as a
logistic function of shot context features (distance, angle, body part,
situation). This is the standard, interpretable xG baseline. The target is the
binary goal indicator; the loss is the mean binary cross-entropy with optional
per-example weights to address the heavy class imbalance (most shots are missed).

Fitting is plain batch gradient descent on the weights and bias with optional L2
regularisation, implemented here rather than delegated, so the model owns its
optimisation and we can verify that the loss decreases and the gradient is
nonzero during training. Standardisation statistics are fit on the training set
only and stored, so transforming a validation or test shot uses training-time
means and scales (no leakage through feature scaling).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class LogisticXG:
    l2: float = 1e-4
    lr: float = 0.5
    epochs: int = 400
    weight: np.ndarray | None = field(default=None, init=False)
    bias: float = field(default=0.0, init=False)
    mean_: np.ndarray | None = field(default=None, init=False)
    scale_: np.ndarray | None = field(default=None, init=False)
    loss_history: list[float] = field(default_factory=list)

    def _standardise(self, x: np.ndarray, fit: bool) -> np.ndarray:
        if fit:
            self.mean_ = x.mean(axis=0)
            self.scale_ = x.std(axis=0)
            self.scale_[self.scale_ == 0] = 1.0
        assert self.mean_ is not None and self.scale_ is not None
        return (x - self.mean_) / self.scale_

    def fit(
        self, x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None
    ) -> LogisticXG:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        xs = self._standardise(x, fit=True)
        n, d = xs.shape
        w = np.zeros(d)
        b = 0.0
        sw = np.ones(n) if sample_weight is None else np.asarray(sample_weight, dtype=float)
        sw = sw / sw.mean()
        self.loss_history = []
        for _ in range(self.epochs):
            z = xs @ w + b
            p = _sigmoid(z)
            # weighted BCE gradient
            err = (p - y) * sw
            grad_w = xs.T @ err / n + self.l2 * w
            grad_b = err.mean()
            w -= self.lr * grad_w
            b -= self.lr * grad_b
            loss = _weighted_bce(y, p, sw) + 0.5 * self.l2 * float(w @ w)
            self.loss_history.append(loss)
        self.weight = w
        self.bias = float(b)
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.weight is None:
            raise RuntimeError("model is not fitted")
        xs = self._standardise(np.asarray(x, dtype=float), fit=False)
        return _sigmoid(xs @ self.weight + self.bias)

    def gradient_norm_at_init(self, x: np.ndarray, y: np.ndarray) -> float:
        """Norm of the loss gradient at zero weights, used as a learning check."""
        xs = self._standardise(np.asarray(x, dtype=float), fit=True)
        p = np.full(len(y), 0.5)
        grad_w = xs.T @ (p - np.asarray(y, dtype=float)) / len(y)
        return float(np.linalg.norm(grad_w))


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _weighted_bce(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> float:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(np.mean(w * -(y * np.log(p) + (1 - y) * np.log(1 - p))))
