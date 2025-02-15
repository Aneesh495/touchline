"""Acceptance campaign: produce a verifiable evidence bundle.

The acceptance runner executes the sample-scale campaign into a fresh evidence
directory: it trains the xG model, records the frozen probe and the claimed
metric, writes feature/shot/sim records that the verifier recomputes, and emits a
manifest with source and environment identities. The summariser that writes these
records is deliberately distinct from the verifier that checks them.
"""

from touchline.acceptance.run import run_acceptance

__all__ = ["run_acceptance"]
