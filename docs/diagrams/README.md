# Diagrams

Editable Mermaid sources (`.mmd`) with rendered SVG exports under `svg/`.
Regenerate with `scripts/render_diagrams.sh` (needs node/npx). Keep the sources in
sync with the code; the SVGs are checked in so the README and docs render without a
build step.

| File | Covers |
|------|--------|
| 01-system-context | sources to interface and verification |
| 02-components | package layer dependencies |
| 03-chronology-leakage | which facts may inform a prediction origin |
| 04-possession-state | possession control state machine |
| 05-masked-spatial-encoder | Deep Sets masked player encoding |
| 06-action-value-target | before/after action value with turnover flip |
| 07-expected-threat | grid value iteration with absorbing outcomes |
| 08-hierarchical-strength | exposure-aware shrinkage |
| 09-season-rule-execution | correlated-draw season simulation |
| 10-evidence-lineage | evidence bundle to independent verifier |
| 11-failure-recovery | resumable job checkpointing |
| 12-shot-to-xg-path | one shot from JSON to served xG |
