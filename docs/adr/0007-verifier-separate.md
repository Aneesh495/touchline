# ADR 0007: Verifier separate from the result summariser

## Status
Accepted.

## Context
If the code that checks results shares a path with the code that produced them, a
bug or a shortcut can pass unnoticed because both sides make the same mistake.

## Decision
Implement the verifier in its own module that recomputes decisive quantities from
raw records and replays saved model weights with its own forward pass. It never
imports the training model for the replay and never trusts a stored pass flag.

## Alternatives
- Reuse the model's predict method in the verifier: convenient but defeats the
  independence the verifier exists to provide.

## Consequences
A broken training routine cannot hide behind a shared code path. The cost is a
small duplicated forward pass, which is the point.
