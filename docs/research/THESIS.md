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

## 3b. What the real-data campaign added

Acquisition then ran at scale: 25,009 unique real league matches across the five
leagues (2010-2024) from football-data.co.uk, and 142 StatsBomb event matches
parsing to 551,204 real on-ball events. On this real data:

- The rules engine reproduced 69 completed league tables with the correct champions
  and standings (verified against the public record, including Leicester 2015-16).
- A rolling-origin Elo forecast beat the base rate on held-out matches in all five
  leagues.
- 44 Dixon-Coles season models beat the base rate on 37 of 44 within-season
  holdouts and placed the real champion in the top-3 attack in 42 of 44.
- The three xG families all beat the base rate on a chronological held-out season;
  boosting led and the neural MLP did not reliably beat the logistic baseline.

These are genuine, verifiable results on real data, not synthetic.

## 4. What is open

Hypotheses H2 through H12 and the hierarchical-transfer question Q2 are partially
exercised (the machinery and splits are implemented and tested) but their full
confirmatory evaluation, the complete 240-cell run matrix, UCL bracket reproduction
across eras, and remote full-profile acceptance remain open, bounded by data breadth
and compute. The blocked items are recorded honestly in `docs/BUILD_STATUS.md`, and
the production line floor (30k) is not met at roughly 7,100 substantive lines.

## 5. Honesty posture

Nothing here is presented as more complete than it is. Synthetic data is labelled
synthetic and never counted toward a real-data gate. Null results are kept. Blocked
gates are blocked, not relabelled. The verifier exists precisely so a reader does
not have to take the results on trust.

See `METHODS.md` for derivations, `RUN_INDEX.md` for the runs, `NEGATIVE_RESULTS.md`
for the nulls, `CONCLUSIONS.md` for scoped conclusions, and `CLAIM_EVIDENCE.md` for
the claim-to-evidence matrix.
