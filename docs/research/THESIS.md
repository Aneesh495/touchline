# Touchline: a synthesis

This report ties the pieces together: what Touchline models, how it keeps itself
honest, and what it has and has not shown. It is written to be read as a whole; the
focused writeups under `writeups/` carry the detail and the per-topic evidence.

## 1. Problem

Football is a continuous spatial game, but most of its data is sparse: results are
everywhere, on-ball events exist for a subset of matches, and full spatial context
is rare. Touchline builds models that respect this unevenness. It values shots
(expected goals), values actions in a possession (their effect on scoring and
conceding), estimates team strength and its evolution, and turns that strength into
a distribution over competition outcomes, all while respecting the knowledge
available at each prediction's origin.

## 2. Method in brief

The domain core keeps match time, pitch geometry, and identifiers honest: periods
and shootouts stay distinct, coordinates grow toward the attacking goal, and ids
remember their provider. Features carry a knowledge time so leakage is a checkable
condition. Models are original and own their targets: logistic and neural xG, a
grid expected-threat solve, a before/after action value, Elo and Dixon-Coles for
team strength, a masked spatial set encoder, a causal sequence encoder, and
empirical-Bayes shrinkage for player rates. The simulator applies era-specific
rules and draws correlated seasons with Monte Carlo error. A registry versions
models with their supported fields; serving is bounded and local; a separate
verifier recomputes and replays rather than trusting stored flags.

## 3. What the evidence shows (diagnostic scale)

Three findings stand on the CPU diagnostic profile with synthetic data, exercising
the full protocol (seeds, splits, bootstrap, proper scores):

- A linear xG is a strong, well-calibrated baseline; on synthetic diagnostic data
  the neural model trains cleanly but does not beat it (H1 null at that scale).
- On 3,562 real La Liga shots with a chronological split, all three learned xG
  families beat the base rate (log loss 0.391); the gradient-boosted model leads
  (0.351), the logistic baseline is strong (0.364), and the neural MLP is unstable
  across seeds and does not reliably beat the logistic model. The honest H1 answer
  on real data is that boosting's non-linearity helps while the neural MLP does not
  consistently win on these tabular features.
- A point-estimate forecast overstates confidence; correlated strength draws lower
  the favourite's title probability from 0.924 to 0.881 and are the honest choice.
- The verifier catches every semantic negative control (leakage, flipped pitch,
  altered labels, impossible qualification) plus a tampered metric and a missing
  artifact, each by recomputation.

## 4. What is open

The confirmatory, real-data evaluation of H1 and the hierarchical-transfer question
Q2, and hypotheses H2 through H12, are open. They require the full-scale data
campaign, which is blocked in a single build session by acquisition volume and
compute. The acquisition path is implemented and verified against live StatsBomb
open data; the blocked gates are recorded honestly in `docs/BUILD_STATUS.md`.

## 5. Honesty posture

Nothing here is presented as more complete than it is. Synthetic data is labelled
synthetic and never counted toward a real-data gate. Null results are kept. Blocked
gates are blocked, not relabelled. The verifier exists precisely so a reader does
not have to take the results on trust.

See `METHODS.md` for derivations, `RUN_INDEX.md` for the runs, `NEGATIVE_RESULTS.md`
for the nulls, `CONCLUSIONS.md` for scoped conclusions, and `CLAIM_EVIDENCE.md` for
the claim-to-evidence matrix.
