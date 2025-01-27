"""Grid-based expected threat (xT).

Expected threat assigns each pitch cell a value equal to the probability that
possession starting there leads to a goal before it is lost, under the empirical
move and shot behaviour observed in the data. It is the classical formulation
(Karun Singh) made explicit here with absorbing outcomes.

For a cell ``z`` the value is

    V(z) = shoot(z) * goal_if_shoot(z)
         + (1 - shoot(z)) * sum_z' move(z -> z') * V(z')

where ``shoot(z)`` is the probability of shooting rather than moving from ``z``,
``goal_if_shoot(z)`` is the chance a shot from ``z`` scores, and
``move(z -> z')`` is the transition distribution of successful moves. Losing the
ball is an absorbing state with value zero, reached implicitly because the move
probabilities from a cell need not sum to one (the deficit is the turnover
probability). The linear system is solved by value iteration, which converges
because the move operator is a sub-stochastic contraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ExpectedThreatGrid:
    n_x: int = 16
    n_y: int = 12
    shoot_prob: np.ndarray | None = field(default=None, init=False)
    goal_prob: np.ndarray | None = field(default=None, init=False)
    value: np.ndarray | None = field(default=None, init=False)
    move_matrix: np.ndarray | None = field(default=None, init=False)  # (C, C)
    converged_iters: int = field(default=0, init=False)

    @property
    def n_cells(self) -> int:
        return self.n_x * self.n_y

    def cell_index(self, x: float, y: float) -> int:
        ix = min(int(x * self.n_x), self.n_x - 1)
        iy = min(int(y * self.n_y), self.n_y - 1)
        return ix * self.n_y + iy

    def fit(
        self,
        shoot_counts: np.ndarray,
        move_counts: np.ndarray,
        goals: np.ndarray,
        shots: np.ndarray,
        move_transitions: np.ndarray,
        max_iter: int = 1000,
        tol: float = 1e-9,
    ) -> ExpectedThreatGrid:
        """Fit from aggregated counts.

        Parameters are per-cell counts: shots taken, moves made, goals, and a
        (C, C) matrix of successful move transitions. Probabilities are formed with
        a small Laplace smoothing so empty cells are defined. The move transition
        rows are scaled by the move probability and the per-move success rate, so a
        cell that usually turns the ball over has little onward value.
        """
        c = self.n_cells
        actions = shoot_counts + move_counts + 1e-9
        self.shoot_prob = shoot_counts / actions
        move_prob = move_counts / actions
        self.goal_prob = goals / (shots + 1e-9)

        # Row-normalise observed transitions into a stochastic move kernel, then
        # scale by the move probability so the operator is sub-stochastic (the
        # remaining mass is the implicit turnover to the zero-value absorbing set).
        row_sums = move_transitions.sum(axis=1, keepdims=True)
        kernel = np.divide(
            move_transitions,
            row_sums,
            out=np.zeros_like(move_transitions),
            where=row_sums > 0,
        )
        self.move_matrix = kernel * move_prob[:, None]

        v = np.zeros(c)
        shoot_term = self.shoot_prob * self.goal_prob
        iters = 0
        for iters in range(1, max_iter + 1):  # noqa: B007 - value kept as converged_iters
            v_new = shoot_term + self.move_matrix @ v
            if np.max(np.abs(v_new - v)) < tol:
                v = v_new
                break
            v = v_new
        self.value = v
        self.converged_iters = iters
        return self

    def value_at(self, x: float, y: float) -> float:
        if self.value is None:
            raise RuntimeError("grid not fitted")
        return float(self.value[self.cell_index(x, y)])

    def value_grid(self) -> np.ndarray:
        if self.value is None:
            raise RuntimeError("grid not fitted")
        return self.value.reshape(self.n_x, self.n_y)
