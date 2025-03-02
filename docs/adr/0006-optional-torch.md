# ADR 0006: Optional torch dependency

## Status
Accepted.

## Context
PyTorch is heavy and its wheels are not available for every Python version and
platform. The domain core, baselines, simulator, and verifier do not need it.

## Decision
Make torch an optional extra. Neural models import it lazily through a
`require_torch` helper that raises a clear install hint if it is missing. Tests that
need torch skip cleanly when it is absent.

## Alternatives
- Require torch always: blocks installation on hosts without a wheel for no benefit
  to the non-neural paths.

## Consequences
The core installs and runs anywhere; neural models are opt-in. The campaign records
a neural run as blocked rather than failing when torch is absent.
