"""Neural spatial/context xG model.

A small multilayer perceptron on the always-available shot features. It is the
neural counterpart of the logistic baseline and exists so the first scientific
question (does non-linear spatial context beat a tabular baseline) can be tested
with matched inputs. It owns its training loop, exposes the loss history and a
gradient-movement check, and trains from random initialisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from touchline.models.neural import require_torch


@dataclass
class SpatialXG:
    hidden: tuple[int, ...] = (32, 16)
    lr: float = 1e-2
    epochs: int = 300
    weight_decay: float = 1e-4
    seed: int = 0
    loss_history: list[float] = field(default_factory=list)
    _model: object = field(default=None, init=False)
    _mean: np.ndarray | None = field(default=None, init=False)
    _scale: np.ndarray | None = field(default=None, init=False)

    def _build(self, in_dim: int):
        torch = require_torch()
        torch.manual_seed(self.seed)
        layers = []
        prev = in_dim
        for h in self.hidden:
            layers += [torch.nn.Linear(prev, h), torch.nn.ReLU()]
            prev = h
        layers += [torch.nn.Linear(prev, 1)]
        return torch.nn.Sequential(*layers)

    def fit(self, x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None):
        torch = require_torch()
        x = np.asarray(x, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)
        self._mean = x.mean(axis=0)
        self._scale = x.std(axis=0)
        self._scale[self._scale == 0] = 1.0
        xs = (x - self._mean) / self._scale
        xt = torch.tensor(xs)
        yt = torch.tensor(y).unsqueeze(1)
        wt = (
            torch.tensor(np.asarray(sample_weight, dtype=np.float32)).unsqueeze(1)
            if sample_weight is not None
            else torch.ones_like(yt)
        )
        self._model = self._build(x.shape[1])
        opt = torch.optim.Adam(
            self._model.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        loss_fn = torch.nn.BCEWithLogitsLoss(reduction="none")
        self.loss_history = []
        for _ in range(self.epochs):
            opt.zero_grad()
            logits = self._model(xt)
            loss = (loss_fn(logits, yt) * wt).mean()
            loss.backward()
            opt.step()
            self.loss_history.append(float(loss.item()))
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        torch = require_torch()
        if self._model is None:
            raise RuntimeError("model not fitted")
        xs = (np.asarray(x, dtype=np.float32) - self._mean) / self._scale
        with torch.no_grad():
            logits = self._model(torch.tensor(xs))
            return torch.sigmoid(logits).squeeze(1).numpy()

    def total_param_norm(self) -> float:
        """Sum of parameter norms, used to show parameters actually changed."""
        torch = require_torch()
        with torch.no_grad():
            return float(
                sum(p.norm().item() for p in self._model.parameters())
            )
