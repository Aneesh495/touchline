"""Masked permutation-invariant set encoder over visible players.

A 360 freeze frame lists the players visible at the moment of a shot: for each,
their location and whether they are a teammate. The number of visible players
varies, some are occluded, and the order carries no meaning. The encoder must
therefore be invariant to player order and must handle a variable number of
players with an explicit mask for missing slots.

The architecture is a Deep Sets style encoder: each player is embedded by a shared
MLP phi, the embeddings are pooled by a masked mean (so padded slots contribute
nothing), and the pooled vector is combined with the ball features through a head
rho. Masked-mean pooling is permutation invariant by construction, which the test
suite checks directly by shuffling players. The context-removal ablation zeroes
the player set to quantify how much the spatial context contributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from touchline.models.neural import require_torch


def _build_player_batch(
    frames: list[list[tuple[float, float, int]]], max_players: int
):
    """Pack variable-length player lists into a padded (B, P, 3) array and mask.

    Each player is (x, y, is_teammate). Returns (players, mask) where mask is 1 for
    real players and 0 for padding.
    """
    b = len(frames)
    players = np.zeros((b, max_players, 3), dtype=np.float32)
    mask = np.zeros((b, max_players), dtype=np.float32)
    for i, frame in enumerate(frames):
        for j, (x, y, mate) in enumerate(frame[:max_players]):
            players[i, j] = (x, y, float(mate))
            mask[i, j] = 1.0
    return players, mask


@dataclass
class MaskedSetEncoder:
    max_players: int = 22
    ball_dim: int = 2
    phi_hidden: int = 32
    embed_dim: int = 24
    rho_hidden: int = 32
    lr: float = 5e-3
    epochs: int = 200
    seed: int = 0
    loss_history: list[float] = field(default_factory=list)
    _net: object = field(default=None, init=False)

    def _build(self):
        torch = require_torch()
        nn = torch.nn
        torch.manual_seed(self.seed)

        class Net(nn.Module):
            def __init__(self, ball_dim, phi_hidden, embed_dim, rho_hidden):
                super().__init__()
                self.phi = nn.Sequential(
                    nn.Linear(3, phi_hidden),
                    nn.ReLU(),
                    nn.Linear(phi_hidden, embed_dim),
                    nn.ReLU(),
                )
                self.rho = nn.Sequential(
                    nn.Linear(embed_dim + ball_dim, rho_hidden),
                    nn.ReLU(),
                    nn.Linear(rho_hidden, 1),
                )

            def forward(self, players, mask, ball):
                # players: (B, P, 3), mask: (B, P), ball: (B, ball_dim)
                emb = self.phi(players)  # (B, P, E)
                m = mask.unsqueeze(-1)  # (B, P, 1)
                summed = (emb * m).sum(dim=1)  # (B, E)
                counts = m.sum(dim=1).clamp(min=1.0)  # (B, 1)
                pooled = summed / counts  # masked mean -> permutation invariant
                h = torch.cat([pooled, ball], dim=1)
                return self.rho(h)

        return Net(self.ball_dim, self.phi_hidden, self.embed_dim, self.rho_hidden)

    def fit(
        self,
        frames: list[list[tuple[float, float, int]]],
        ball: np.ndarray,
        y: np.ndarray,
    ):
        torch = require_torch()
        players, mask = _build_player_batch(frames, self.max_players)
        ball = np.asarray(ball, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)
        pt = torch.tensor(players)
        mt = torch.tensor(mask)
        bt = torch.tensor(ball)
        yt = torch.tensor(y).unsqueeze(1)
        self._net = self._build()
        opt = torch.optim.Adam(self._net.parameters(), lr=self.lr)
        loss_fn = torch.nn.BCEWithLogitsLoss()
        self.loss_history = []
        for _ in range(self.epochs):
            opt.zero_grad()
            logits = self._net(pt, mt, bt)
            loss = loss_fn(logits, yt)
            loss.backward()
            opt.step()
            self.loss_history.append(float(loss.item()))
        return self

    def predict_proba(
        self, frames: list[list[tuple[float, float, int]]], ball: np.ndarray
    ) -> np.ndarray:
        torch = require_torch()
        players, mask = _build_player_batch(frames, self.max_players)
        with torch.no_grad():
            logits = self._net(
                torch.tensor(players),
                torch.tensor(mask),
                torch.tensor(np.asarray(ball, dtype=np.float32)),
            )
            return torch.sigmoid(logits).squeeze(1).numpy()

    def predict_without_players(self, ball: np.ndarray) -> np.ndarray:
        """Context-removal ablation: predict with an empty player set."""
        frames = [[] for _ in range(len(ball))]
        return self.predict_proba(frames, ball)
