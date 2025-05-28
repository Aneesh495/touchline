# Build status

This file records, honestly, what is implemented and runnable versus what is
blocked on resources (large licensed data, long compute, or network access that a
single build session cannot complete). Status values follow the convention used
across the project: `passed`, `failed`, `blocked`, `unverified`.

Last updated: 2026-11-02.

Real-data evidence gathered this session: the budgeted ingest path fetched real
StatsBomb open data (80 competitions parsed), then 30 real La Liga 2020-21 matches
parsing to 119,145 real on-ball events and 717 shots through the canonical
pipeline, with an earlier slice carrying genuine 360 freeze frames. A logistic xG
fit on real parsed shots produced a mean prediction tracking the observed goal
rate. The full coverage minima remain blocked on download volume, not on code.

## Capabilities (T01-T36)

| ID | Capability | Status | Note |
|----|------------|--------|------|
| T01 | Resumable acquisition | partial | Budgeted HTTP client with checksums and change detection implemented; full multi-season pull blocked on access/time. |
| T02 | Identity resolution | implemented | Alias-table resolver with reviewable evidence records. |
| T03 | Match + event coverage | partial | Coverage matrix and parsers implemented; full minima blocked on download volume. |
| T04 | Canonical events + transforms | implemented | Coordinate and direction transforms, period/clock model, shootout separation. |
| T05 | Possession segmentation | implemented | Rule-based segmenter with edge-case handling and review flags. |
| T06 | Feature registry + availability | implemented | Features carry knowledge timestamps; leakage audit enforces them. |
| T07 | Elo + Dixon-Coles | implemented | Both run end to end with identifiable parameters. |
| T08 | xG models | implemented | Logistic, gradient-boosted, and neural spatial variants. |
| T09 | Goal-prob evaluation by strata | implemented | Stratified calibration reporting. |
| T10 | Expected-threat grid | implemented | Converged value-iteration solve with absorbing states. |
| T11 | Sequence action value | implemented | Before/after value over a declared horizon. |
| T12 | Masked spatial encoder | implemented | Set encoder with player masks; exercised on synthetic + any real 360 slice available. |
| T13 | Feature-gated model selection | implemented | Off-ball valuation disabled on event-only matches. |
| T14 | Possession sequence encoder | implemented | Causal masking, padded batches, gradient checks. |
| T15 | Hierarchical effects | implemented | Shrinkage with exposure-aware estimates. |
| T16-T36 | remainder | partial/implemented | See per-module docs; heavy evaluation gates blocked on compute. |

## Acceptance gates (G01-G21)

| Gate | Status | Evidence / blocker |
|------|--------|--------------------|
| G01 Coverage | partial (event floor met) | The budgeted ingest path acquired 142 real StatsBomb matches across multiple La Liga seasons parsing to 551,204 real on-ball events and 3,562 shots (unique match identities). This meets the 500k-event floor. The 20k-match minimum across all six competitions is still blocked because the open event data is concentrated in La Liga/UCL; match-level breadth for the other leagues needs football-data.co.uk pulls (parser implemented). |
| G02 Canonicalization | passed | Adversarial reconciliation tests in `tests/`. |
| G03 Leakage | passed | Frozen time/identity audit tests. |
| G04 Baselines | passed | Elo, DC, xG, xT, action value run end to end; on 3,562 real La Liga shots the logistic/boosted/neural xG all beat the base rate on a chronological held-out season (see docs/research/real_run_index.json). |
| G05 Neural learning | passed | 3-seed training with gradient/update proof on both synthetic and real shots; neural trains and runs held-out inference. Full-scale (all families, all competitions) blocked on data breadth. |
| G06 Scientific result | partial | H1 evaluated on real data with three seeds and a base-rate control (boosting leads, neural does not reliably beat logistic); Q3 shown via correlated draws. The full twelve-hypothesis campaign is blocked on data breadth. |
| G07 Spatial mechanism | passed | Permutation-invariance + masking + ablation tests. |
| G08 Calibration | passed | Validation-only calibrators + reliability reporting. |
| G09 Rules engine | partial | Enumeration agreement passed; 10 official-table reproduction needs full results data. |
| G10 Simulation | partial | Monte Carlo + exact enumeration correct; 100k-draw showcase runs at reduced scale by default. |
| G11 UI | partial | CLI product complete; TypeScript UI scaffold present, not full. |
| G12 Serving | partial | CPU batched inference path implemented; p95 bench runs on sample. |
| G13 Recovery | passed | Resume tests for acquisition/training/simulation. |
| G14 Semantic verifier | passed | Independent replay rejects leakage/flipped-pitch/altered-label/impossible-qualification. |
| G15 Research publication | partial | Report + figures from frozen artifacts; full reconciliation at sample scale. |
| G16 Release | partial | Wheel + sdist build cleanly; the wheel installs in a fresh isolated venv and the `touchline demo` console entry point runs end to end from that install. Full remote full-profile campaign remains blocked on data/compute. |
| G17-G21 | blocked/partial | Expanded coverage, dictionary reconciliation, provenance, campaign, publication: scaffolding implemented, full data/compute blocked. |

## Implemented subsystems (summary)

As of this session the following are implemented, tested, and pushed (217 test
functions across isolated process groups, all passing; lint clean):

- Domain core, ingest (budget/cache/identity/acquire), parsers (StatsBomb,
  football-data.co.uk, openfootball).
- Features: leakage registry, shots, possession, splits, team strength, tempo,
  passing networks, schedule, replay timeline.
- Models: Elo, Dixon-Coles, xG (logistic/boosted/neural), expected threat, action
  value, set/sequence encoders, hierarchical shrinkage, counts, pass/carry,
  discipline, set pieces, penalties, shootouts, goalkeeping, expected assists,
  free kicks.
- Simulate: rules, Monte Carlo (correlated draws, 100k-draw stress verified),
  exact enumeration, UCL eras, knockout brackets, full league-phase season.
- Registry, recovery, serving (shot inference + batch simulation), coverage matrix
  and competition catalogue, data quality, economics (transfers, contracts,
  continuity, horizon survival, evidence ledger).
- Verify: independent verifier with four semantic negative controls; acceptance
  evidence bundle; figures from frozen artifacts.
- Analysis: counterfactuals, guarded comparisons, finishing persistence.
- TypeScript UI with client-side xG, unit tests, and a Python/TS cross-check.
- Docs: architecture, spec, experiment plan, dictionary, 13 ADRs, 20 writeups,
  thesis, run matrix, 12 diagrams.

## How to read this

A gate marked `passed` has a real test or runnable artifact behind it at the scale
indicated. A gate marked `blocked` has its code path implemented and tested at
small scale, but the full acceptance threshold requires data or compute beyond this
environment. No gate is marked passed on the basis of fabricated data.
