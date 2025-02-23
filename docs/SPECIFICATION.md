# Specification

This document states the problem Touchline addresses, the objects it models, and
the contracts each subsystem honours. It is the reference the code is written
against; `docs/BUILD_STATUS.md` tracks how much of it is implemented.

## Problem

Given permitted match results and, for a smaller subset, on-ball event and
occasional spatial data across the major European leagues and the Champions
League, estimate:

1. the value of a shot (expected goals),
2. the value of an action in a possession (its effect on scoring and conceding),
3. team strength and its evolution, and
4. the distribution of competition outcomes (title, qualification, relegation)
   under that uncertainty,

while respecting the knowledge available at each prediction's origin so no future
information leaks into an earlier forecast.

## Objects

| Object | Fields of record |
|--------|------------------|
| MatchClock | period, second-in-period, added (stoppage) second |
| Point | canonical x, y growing toward the attacking goal |
| Shot | location, body part, penalty/shootout flags, situation, goal label |
| Event | index, clock, type, team, player, location, possession id, raw payload |
| Possession | team, start/end index and clock, event count, review flag |
| Match | competition, season, teams, venue, phase-split score, appearances, events |
| ScoreState | regulation / extra-time / shootout goals, kept separate |

## Three frozen questions

1. Does spatial sequence context improve calibrated action value over a tabular
   baseline?
2. Does hierarchical club/league structure improve transfer to an unseen
   competition or season?
3. How does uncertainty in team strength change qualification forecasts?

Each is predeclared in `docs/research/HYPOTHESES.md` with endpoints and negative
controls. An honest null result is acceptable; broken training or absent
evaluation is not.

## Contracts

- **Time:** every feature carries a knowledge time; the registry rejects any
  feature not knowable at the prediction origin.
- **Units:** distances are metres on a nominal 105x68 pitch; angles are radians;
  rates are per-90 unless stated otherwise.
- **Identifiers:** provider-scoped; cross-provider links are auditable evidence.
- **Calibration:** calibrators fit on validation only; out-of-support inputs get a
  visible limited-support status.
- **Selection:** model selection never inspects final test performance; the rule
  is recorded on the model card.
- **Simulation:** correlated strength draws per season, Monte Carlo error bars,
  exact enumeration for small tournaments.

## Acceptance

Gates G01-G21 are defined in `docs/BUILD_STATUS.md` with their current status and
the evidence or blocker behind each. The verifier in `touchline.verify` recomputes
the decisive quantities and runs semantic negative controls rather than trusting
stored flags.
