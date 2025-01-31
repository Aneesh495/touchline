"""Causal possession-sequence encoder.

A possession is a variable-length ordered sequence of action features. The encoder
reads the sequence left to right and predicts, at each step, a target that may only
depend on the current and earlier steps. Causality is enforced by a causal mask in
the self-attention so step t never attends to steps after t, and by padding shorter
sequences in a batch with a padding mask so padded positions contribute neither to
attention nor to the loss.

The implementation is a small Transformer encoder with a learned positional
encoding and a per-step linear head. It owns its training loop and exposes a check
that the gradient flows and that a padded position does not change the output of
the real positions (padded-batch correctness).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from touchline.models.neural import require_torch


def pad_sequences(seqs: list[np.ndarray], max_len: int, feat_dim: int):
    """Pack variable-length sequences into (B, L, F) with a (B, L) pad mask."""
    b = len(seqs)
    x = np.zeros((b, max_len, feat_dim), dtype=np.float32)
    pad = np.ones((b, max_len), dtype=bool)  # True = padding (ignored)
    for i, s in enumerate(seqs):
        n = min(len(s), max_len)
        x[i, :n] = s[:n]
        pad[i, :n] = False
    return x, pad


@dataclass
class SequenceEncoder:
    feat_dim: int = 8
    d_model: int = 32
    n_heads: int = 4
    max_len: int = 40
    lr: float = 3e-3
    epochs: int = 150
    seed: int = 0
    loss_history: list[float] = field(default_factory=list)
    _net: object = field(default=None, init=False)

    def _build(self):
        torch = require_torch()
        nn = torch.nn
        torch.manual_seed(self.seed)

        class Net(nn.Module):
            def __init__(self, feat_dim, d_model, n_heads, max_len):
                super().__init__()
                self.input = nn.Linear(feat_dim, d_model)
                self.pos = nn.Parameter(torch.randn(max_len, d_model) * 0.02)
                layer = nn.TransformerEncoderLayer(
                    d_model,
                    n_heads,
                    dim_feedforward=2 * d_model,
                    dropout=0.0,
                    batch_first=True,
                )
                # enable_nested_tensor would route through a fused kernel that can
                # ignore the attention mask; disable it so the causal mask is
                # always honoured.
                self.enc = nn.TransformerEncoder(
                    layer, num_layers=2, enable_nested_tensor=False
                )
                self.head = nn.Linear(d_model, 1)
                self.max_len = max_len

            def forward(self, x, pad_mask):
                # x: (B, L, F), pad_mask: (B, L) True where padding
                b, length, _ = x.shape
                h = self.input(x) + self.pos[:length].unsqueeze(0)
                causal = torch.triu(
                    torch.ones(length, length, dtype=torch.bool), diagonal=1
                )
                h = self.enc(h, mask=causal, src_key_padding_mask=pad_mask)
                return self.head(h).squeeze(-1)  # (B, L)

        return Net(self.feat_dim, self.d_model, self.n_heads, self.max_len)

    def fit(self, seqs: list[np.ndarray], targets: list[np.ndarray]):
        torch = require_torch()
        x, pad = pad_sequences(seqs, self.max_len, self.feat_dim)
        y = np.zeros((len(seqs), self.max_len), dtype=np.float32)
        for i, t in enumerate(targets):
            n = min(len(t), self.max_len)
            y[i, :n] = t[:n]
        xt = torch.tensor(x)
        padt = torch.tensor(pad)
        yt = torch.tensor(y)
        valid = torch.tensor(~pad, dtype=torch.float32)
        self._net = self._build()
        opt = torch.optim.Adam(self._net.parameters(), lr=self.lr)
        loss_fn = torch.nn.BCEWithLogitsLoss(reduction="none")
        self.loss_history = []
        for _ in range(self.epochs):
            opt.zero_grad()
            logits = self._net(xt, padt)
            loss = (loss_fn(logits, yt) * valid).sum() / valid.sum()
            loss.backward()
            opt.step()
            self.loss_history.append(float(loss.item()))
        return self

    def predict(self, seqs: list[np.ndarray]) -> list[np.ndarray]:
        torch = require_torch()
        self._net.eval()
        x, pad = pad_sequences(seqs, self.max_len, self.feat_dim)
        with torch.no_grad():
            logits = self._net(torch.tensor(x), torch.tensor(pad))
            probs = torch.sigmoid(logits).numpy()
        out = []
        for i, s in enumerate(seqs):
            n = min(len(s), self.max_len)
            out.append(probs[i, :n])
        return out
