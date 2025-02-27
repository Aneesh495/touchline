# Glossary

Terms used across Touchline, defined once.

- **xG (expected goals):** the modelled probability that a shot becomes a goal.
- **xT (expected threat):** the probability that possession starting in a pitch cell
  leads to a goal before it is lost.
- **action value:** the change in the controlling team's score-minus-concede
  probability caused by an action, over a declared horizon.
- **knowledge time:** the moment a fact became known; a feature may inform a
  prediction only at or after its knowledge time.
- **group integrity:** the property that no competition-season appears in both the
  train and test split.
- **calibration:** agreement between predicted probabilities and observed
  frequencies.
- **reliability table:** predictions binned and compared to observed rates per bin.
- **Brier score / log loss:** proper scoring rules for probabilistic predictions.
- **shrinkage (partial pooling):** pulling a noisy per-entity estimate toward the
  population mean by an amount set by its exposure.
- **exposure:** the sample (e.g. minutes played) behind a per-entity estimate.
- **correlated draws:** sampling team strength once per simulated season so a team's
  matches are correlated through its draw.
- **Monte Carlo error:** the standard error of a probability estimated from a finite
  number of simulations.
- **field level:** the data depth available for a match: results, events, or
  tracking.
- **semantic negative control:** a deliberately corrupted evidence bundle used to
  confirm the verifier rejects for a meaningful reason.
