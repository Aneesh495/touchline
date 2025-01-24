"""A Dixon-Coles style match-score model.

The model treats home and away goals as (nearly) Poisson with means

    log mu_home = mu + home_adv + attack[home] - defence[away]
    log mu_away = mu + attack[away] - defence[home]

where ``attack`` and ``defence`` are per-team parameters, ``mu`` is a baseline
scoring log-rate and ``home_adv`` is the home scoring boost. The independence of
the two Poisson counts overstates draws and 1-0/0-1 scores, so Dixon and Coles
(1997) introduce a correction ``tau`` on the four lowest scorelines governed by a
dependence parameter ``rho``.

Parameters are fit by maximising the log-likelihood with L-BFGS. An identifiability
constraint (mean attack and mean defence fixed to zero) is applied so the
parameters are interpretable: a positive attack means a team scores more than the
league baseline given the opponent.

From fitted parameters the model produces a full scoreline distribution, and from
that the probabilities of home win, draw, and away win, plus expected goals for
each side. These feed both evaluation and the competition simulator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson


@dataclass
class DixonColesModel:
    max_goals: int = 10
    teams: list[str] = field(default_factory=list)
    attack: dict[str, float] = field(default_factory=dict)
    defence: dict[str, float] = field(default_factory=dict)
    mu: float = 0.0
    home_adv: float = 0.0
    rho: float = 0.0
    fitted: bool = False

    @staticmethod
    def _tau(h: int, a: int, lam: float, mu: float, rho: float) -> float:
        """Dixon-Coles low-score dependence correction."""
        if h == 0 and a == 0:
            return 1.0 - lam * mu * rho
        if h == 0 and a == 1:
            return 1.0 + lam * rho
        if h == 1 and a == 0:
            return 1.0 + mu * rho
        if h == 1 and a == 1:
            return 1.0 - rho
        return 1.0

    def fit(
        self,
        home_teams: list[str],
        away_teams: list[str],
        home_goals: list[int],
        away_goals: list[int],
        weights: np.ndarray | None = None,
        max_iter: int = 200,
    ) -> DixonColesModel:
        teams = sorted(set(home_teams) | set(away_teams))
        self.teams = teams
        idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)
        hg = np.asarray(home_goals, dtype=float)
        ag = np.asarray(away_goals, dtype=float)
        hi = np.array([idx[t] for t in home_teams])
        ai = np.array([idx[t] for t in away_teams])
        w = np.ones_like(hg) if weights is None else np.asarray(weights, dtype=float)

        # params: [attack(n-1 free), defence(n-1 free), mu, home_adv, rho]
        # We parametrise all n attack/defence then enforce sum-zero via projection
        # at read-out; keeping all n with a soft centre is simpler and stable here.
        def unpack(p):
            atk = p[:n]
            dfc = p[n : 2 * n]
            mu, home_adv, rho = p[2 * n], p[2 * n + 1], p[2 * n + 2]
            # centre for identifiability
            atk = atk - atk.mean()
            dfc = dfc - dfc.mean()
            return atk, dfc, mu, home_adv, rho

        def neg_ll(p):
            atk, dfc, mu, home_adv, rho = unpack(p)
            lam = np.exp(mu + home_adv + atk[hi] - dfc[ai])
            muu = np.exp(mu + atk[ai] - dfc[hi])
            ll = w * (
                poisson.logpmf(hg, lam) + poisson.logpmf(ag, muu)
            )
            # low-score correction, vectorised over the four special scorelines
            tau = np.ones_like(lam)
            m00 = (hg == 0) & (ag == 0)
            m01 = (hg == 0) & (ag == 1)
            m10 = (hg == 1) & (ag == 0)
            m11 = (hg == 1) & (ag == 1)
            tau[m00] = 1.0 - lam[m00] * muu[m00] * rho
            tau[m01] = 1.0 + lam[m01] * rho
            tau[m10] = 1.0 + muu[m10] * rho
            tau[m11] = 1.0 - rho
            tau = np.clip(tau, 1e-6, None)
            ll = ll + w * np.log(tau)
            return -ll.sum()

        x0 = np.concatenate(
            [np.zeros(n), np.zeros(n), np.array([0.0, 0.2, -0.05])]
        )
        res = minimize(
            neg_ll, x0, method="L-BFGS-B", options={"maxiter": max_iter}
        )
        atk, dfc, mu, home_adv, rho = unpack(res.x)
        self.attack = {t: float(atk[idx[t]]) for t in teams}
        self.defence = {t: float(dfc[idx[t]]) for t in teams}
        self.mu = float(mu)
        self.home_adv = float(home_adv)
        self.rho = float(rho)
        self.fitted = True
        return self

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        lam = math.exp(
            self.mu + self.home_adv + self.attack.get(home, 0.0) - self.defence.get(away, 0.0)
        )
        mu = math.exp(self.mu + self.attack.get(away, 0.0) - self.defence.get(home, 0.0))
        return lam, mu

    def scoreline_matrix(self, home: str, away: str) -> np.ndarray:
        lam, mu = self.expected_goals(home, away)
        hs = np.arange(self.max_goals + 1)
        ph = poisson.pmf(hs, lam)
        pa = poisson.pmf(hs, mu)
        mat = np.outer(ph, pa)
        # apply low-score correction
        for h in (0, 1):
            for a in (0, 1):
                mat[h, a] *= self._tau(h, a, lam, mu, self.rho)
        mat /= mat.sum()
        return mat

    def result_probs(self, home: str, away: str) -> tuple[float, float, float]:
        mat = self.scoreline_matrix(home, away)
        p_home = float(np.tril(mat, -1).sum())
        p_draw = float(np.trace(mat))
        p_away = float(np.triu(mat, 1).sum())
        return p_home, p_draw, p_away
