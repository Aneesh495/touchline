# Claim-to-evidence matrix

Every behavioural or performance claim maps to the source that implements it, the
test or run that exercises it, and the status. Status uses `passed`, `blocked`, or
`unverified` accurately.

| Claim | Source | Evidence | Status |
|-------|--------|----------|--------|
| Match time keeps periods/stoppage/shootouts distinct | domain/clock.py | tests/test_clock.py | passed |
| Pitch coordinates transform to a canonical attacking frame | domain/geometry.py | tests/test_geometry.py | passed |
| Identifiers are provider-scoped | domain/identifiers.py | tests/test_match.py | passed |
| StatsBomb events parse with correct phase and penalty/shootout split | parse/statsbomb.py | tests/test_parse_statsbomb.py | passed |
| football-data.co.uk CSV parses with per-match stats | parse/football_data_uk.py | tests/test_parse_football_data_uk.py | passed |
| Acquisition is budgeted, cached, and resumable | ingest/acquire.py | tests/test_acquire.py + live fetch | passed |
| Leakage is caught at feature-use time | features/registry.py | tests/test_features.py | passed |
| Chronological splits preserve group integrity | features/splits.py | tests/test_splits_and_strength.py | passed |
| Elo and Dixon-Coles recover known strength ordering | models/elo.py, dixon_coles.py | tests/test_models_baselines.py | passed |
| Logistic xG learns and discriminates | models/xg_logistic.py | tests/test_models_baselines.py | passed |
| Neural xG trains (gradient movement) | models/neural/spatial_xg.py | tests/test_neural.py | passed |
| Set encoder is permutation invariant and mask-correct | models/neural/set_encoder.py | tests/test_neural.py | passed |
| Sequence encoder is causal | models/neural/sequence_encoder.py | tests/test_neural.py | passed |
| Expected threat converges with absorbing outcomes | models/expected_threat.py | tests/test_domain_algorithms.py | passed |
| Action value credits progression | models/action_value.py | tests/test_domain_algorithms.py | passed |
| Shrinkage pulls small samples to the prior | models/hierarchical.py | tests/test_hierarchical.py | passed |
| Simulator matches exact enumeration | simulate/monte_carlo.py | tests/test_simulate.py | passed |
| UCL away-goals and league-phase eras handled | simulate/ucl.py | tests/test_ucl_and_coverage.py | passed |
| Coverage distinguishes depth with unique counts | coverage/matrix.py | tests/test_ucl_and_coverage.py | passed |
| Registry gates spatial models for event-only matches | registry/model_card.py | tests/test_registry.py | passed |
| Recovery resumes without restarting | registry/recovery.py | tests/test_registry.py | passed |
| Serving p95 under 250 ms for 128-shot batches (CPU, sample) | serving/inference.py | tests/test_serving.py | passed |
| Data-quality checks report rather than repair | quality/reconcile.py | tests/test_quality.py | passed |
| Verifier rejects four semantic negative controls | verify/verifier.py | tests/test_verifier_controls.py | passed |
| Neural xG beats logistic on real data (H1 confirmatory) | experiments/campaign.py | real-data campaign | blocked |
| Full coverage minima (20k matches, 500k events) | coverage, ingest | full acquisition | blocked |
| 100k-draw showcase per scenario | simulate | full compute | blocked |
| Remote full-profile acceptance | acceptance, verify | full campaign | blocked |
