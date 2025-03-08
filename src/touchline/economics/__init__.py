"""Squad economics: transfers, loans, and publicly confirmed contracts.

This is a separate connected research domain. It models squad construction and
publicly documented contracts with bitemporal records: when a fact applied and when
it became known. A future contract extension cannot explain an earlier forecast
unless it is labelled retrospective, which the knowledge-time field enforces. Fees
and options that are not public remain unknown rather than being guessed.
"""

from touchline.economics.transfers import (
    ContractRecord,
    FeeInterval,
    TransferRecord,
    TransferType,
    squad_continuity,
)

__all__ = [
    "TransferRecord",
    "ContractRecord",
    "TransferType",
    "FeeInterval",
    "squad_continuity",
]
