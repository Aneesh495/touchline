# Schema and numerical contracts

The precision, units, and ranges every subsystem relies on. Violating one of these
is a bug, and several are enforced by construction (a `Point` out of [0,1] raises).

## Units

| Quantity | Unit | Notes |
|----------|------|-------|
| pitch distance | metres | nominal 105 x 68 pitch |
| shot angle | radians | angle subtended by the goal mouth, in [0, pi] |
| rate (per-90) | events per 90 minutes | denominator is eligible minutes |
| probability | dimensionless in [0, 1] | xG, action value components, forecasts |
| time | (period, second-in-period, added) | not a uniform 90-minute clock |

## Ranges enforced by construction

- Canonical `Point.x`, `Point.y` in [0, 1]; out-of-range raises `ValueError`.
- `MatchClock.second`, `.added` non-negative; shootout has zero added time.
- `Period.number` >= 1.
- `Possession` end index >= start index; event count >= 1.

## Precision

- Models compute in float64 (numpy default) in Python; the UI computes in JS
  double precision. The cross-language xG check confirms agreement to ~1e-16.
- Logistic and sigmoid inputs are clipped to [-30, 30] before exponentiation to
  avoid overflow, which changes outputs by less than 1e-13 in the active range.

## Serialization

- Model artifacts are JSON (weights, bias, feature means and scales, training
  feature ranges) plus a sha256 sidecar; see `registry.artifacts`.
- Evidence bundles are JSON and JSONL with a MANIFEST listing every artifact.
- Provider payloads are preserved verbatim in each domain object's `raw` field, so
  canonicalisation never destroys the original bytes.

## Identifiers

- Provider-scoped; a `TeamId` from one provider never equals one from another.
- Competition codes are Touchline-stable (EPL, UCL, ...); see
  `coverage.competitions`.

## Numerical stability

- Dixon-Coles is fit by L-BFGS with a sum-zero identifiability constraint on
  attack and defence; the tau correction is clipped at 1e-6 to stay positive.
- Expected-threat value iteration converges because the move operator is
  sub-stochastic (row sums below one, the deficit being turnover).
