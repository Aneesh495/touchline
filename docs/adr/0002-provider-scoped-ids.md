# ADR 0002: Provider-scoped identifiers

## Status
Accepted.

## Context
Different providers assign different ids and names to the same real club or player.
Treating a raw id or name as globally unique causes silent wrong merges.

## Decision
Every identifier carries its provider. Two ids are unequal across providers even
with the same value. Cross-provider links are produced only through the identity
resolver, which records method and confidence and queues ambiguous links for
review.

## Alternatives
- A single global id space with a best-effort merge: fast but creates undetectable
  false merges.
- Names as keys: brittle to accents, suffixes, and renames.

## Consequences
Merges are auditable and reversible. The cost is that any cross-provider join must
go through the resolver, which is the intended friction.
