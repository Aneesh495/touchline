# Changelog

All notable changes to Touchline. This project is under active construction; the
first tagged release will follow the full-profile acceptance campaign.

## Unreleased

### Added
- Typed football domain core: non-uniform match clock, canonical pitch geometry,
  provider-scoped identifiers, events/shots/possessions, phase-split score state.
- Ingest: budgeted, checksummed, resumable acquisition; cross-provider identity
  resolution; parsers for StatsBomb open data, football-data.co.uk, and
  openfootball. Verified against live StatsBomb data (119,145 real events parsed).
- Leakage-aware feature layer with a knowledge-time contract, chronological and
  competition-holdout and rolling-origin splits, and a split-integrity audit.
- Models: Elo, Dixon-Coles, logistic/boosted/neural xG, expected threat, action
  value, masked spatial set encoder, causal sequence encoder, hierarchical
  shrinkage, negative-binomial counts, pass/carry/dribble, discipline/manpower,
  set pieces, penalties and shootouts, goalkeeping (eligibility-gated), expected
  assists, free-kick/corner classification.
- Simulator: configurable league rules with era-specific tie-breaks, correlated
  Monte Carlo seasons with error bars, exact small-tournament enumeration,
  era-specific UCL rules, knockout brackets, and a full league-phase-to-knockout
  season. 100,000-draw stress run verified.
- Registry, resumable recovery, bounded CPU serving (shot inference and batch
  season simulation), drift monitoring, coverage matrix and competition catalogue,
  data-quality reconciliation, squad economics with bitemporal records.
- Independent verifier with four semantic negative controls; acceptance evidence
  bundle; research figures from frozen artifacts.
- TypeScript tactical UI (pitch, shot map, client-side xG, coverage indicator,
  keyboard operation) with unit tests and a Python/TS cross-language xG check.
- Documentation: architecture, specification, experiment plan, statistical
  dictionary, 13 ADRs, 20 research writeups, a synthesis thesis, 12 diagrams.

### Findings (diagnostic scale)
- Neural xG does not beat the logistic baseline on these features (H1 null).
- Correlated strength draws widen the forecast (point 0.924 vs correlated 0.881).

### Blocked (data/compute)
- Full coverage minima, the 240-run real-data campaign, and remote full-profile
  acceptance. Code paths implemented and tested at diagnostic scale.
