"""Penalty shootout probabilities, kept separate from regulation penalties.

A shootout is a distinct process: alternating kicks, sudden death after five each,
and per-taker conversion that is not the same as a regulation penalty. This module
computes a shootout win probability from each side's per-kick conversion rate by
exact dynamic programming over the first five kicks plus a geometric sudden-death
tail. Shootout kicks never enter regulation penalty counts (enforced in the
domain), so this is the only place shootout probabilities are produced.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShootoutModel:
    conv_a: float  # team A per-kick conversion
    conv_b: float  # team B per-kick conversion
    best_of: int = 5

    def win_prob_a(self) -> float:
        """Probability team A wins the shootout.

        Enumerate the outcomes of the first ``best_of`` kicks each (A kicks first),
        then resolve ties with a sudden-death round whose win probability is the
        per-round advantage of A over B. This is an approximation that ignores the
        early-stop structure within the first five but is exact for the final
        distribution of made kicks, which is what decides the tie.
        """
        from math import comb

        n = self.best_of
        pa, pb = self.conv_a, self.conv_b
        p_a_wins = 0.0
        p_tie = 0.0
        for ka in range(n + 1):
            pka = comb(n, ka) * pa**ka * (1 - pa) ** (n - ka)
            for kb in range(n + 1):
                pkb = comb(n, kb) * pb**kb * (1 - pb) ** (n - kb)
                joint = pka * pkb
                if ka > kb:
                    p_a_wins += joint
                elif ka == kb:
                    p_tie += joint
        # Sudden death: each round both take one; A wins the round if it scores and
        # B misses; B wins if B scores and A misses; otherwise repeat. The
        # conditional win probability for A is a scores-and-b-misses over not-equal.
        a_round = pa * (1 - pb)
        b_round = pb * (1 - pa)
        denom = a_round + b_round
        sudden_a = a_round / denom if denom > 0 else 0.5
        return p_a_wins + p_tie * sudden_a
