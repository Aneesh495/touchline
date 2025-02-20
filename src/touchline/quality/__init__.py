"""Data-quality investigations.

These checks surface missing or contradictory data rather than papering over it.
They reconcile the score implied by goal events against the recorded final score,
flag matches where a red card is recorded without a corresponding manpower change,
detect lineup gaps (fewer than eleven starters), and report rather than repair.
The philosophy is to report unresolved discrepancies with evidence, never to force
agreement by altering source data.
"""

from touchline.quality.reconcile import (
    DiscrepancyReport,
    check_lineup_completeness,
    check_red_card_manpower,
    reconcile_score,
)

__all__ = [
    "DiscrepancyReport",
    "reconcile_score",
    "check_lineup_completeness",
    "check_red_card_manpower",
]
