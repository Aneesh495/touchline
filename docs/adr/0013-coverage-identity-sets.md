# ADR 0013: Coverage counted from identity sets

## Status
Accepted.

## Context
The same match can arrive from more than one feed. Counting rows would inflate
coverage and overstate how much real data the project has.

## Decision
Count coverage from sets of unique match identities, not row counts. The coverage
matrix stores match-id sets per depth (results, events, tracking) so a duplicated
feed adds nothing.

## Alternatives
- Count rows: simple but inflates and misleads.

## Consequences
Coverage numbers reflect unique real matches, satisfying the gate requirement to
count real identities rather than augmented rows. The cost is holding id sets, which
is cheap at this scale.
