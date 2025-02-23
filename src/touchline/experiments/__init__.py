"""Experiment campaign: registered runs with preserved metrics.

Each run answers a registered question, fixes its seed and split, and records its
metrics into an indexed results table including failures. The campaign here runs
at the CPU diagnostic scale by default; the same harness runs the full profile
over acquired data.
"""

from touchline.experiments.campaign import (
    RunRecord,
    run_strength_uncertainty,
    run_xg_comparison,
)

__all__ = ["RunRecord", "run_xg_comparison", "run_strength_uncertainty"]
