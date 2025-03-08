"""Transfer and contract records with bitemporal integrity.

Every record has two time axes: the ``effective_date`` (when the fact applied, e.g.
the transfer registration date) and the ``known_date`` (when it became public). A
model building features at a prediction origin may only use records whose
``known_date`` is at or before that origin; a later announcement is retrospective
and is labelled as such.

Fees are intervals, not point values, because public reporting is often a range or
unknown. An add-on is kept separate from the base fee. Loans are distinguished from
permanent moves, and a free transfer has a zero-base fee with that fact recorded
rather than a missing value.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TransferType(str, Enum):
    PERMANENT = "permanent"
    LOAN = "loan"
    LOAN_WITH_OPTION = "loan_with_option"
    FREE = "free"
    END_OF_LOAN = "end_of_loan"


@dataclass(frozen=True)
class FeeInterval:
    """A reported fee as a known interval, or unknown.

    ``low`` and ``high`` bound the reported base fee in a stated currency. When the
    fee is undisclosed both are None and ``disclosed`` is False. Add-ons are kept
    separate because they are contingent and often unreported.
    """

    low: float | None
    high: float | None
    currency: str = "EUR"
    disclosed: bool = True
    add_on_high: float | None = None

    @classmethod
    def undisclosed(cls) -> FeeInterval:
        return cls(None, None, disclosed=False)

    @classmethod
    def free(cls) -> FeeInterval:
        return cls(0.0, 0.0)

    def midpoint(self) -> float | None:
        if self.low is None or self.high is None:
            return None
        return (self.low + self.high) / 2.0


@dataclass(frozen=True)
class TransferRecord:
    player: str
    from_club: str | None
    to_club: str
    transfer_type: TransferType
    effective_date: date  # registration / window date the move applied
    known_date: date  # when the move became public
    fee: FeeInterval
    source: str  # provenance: official announcement, registration, etc.
    confidence: float = 1.0

    def known_at(self, origin: date) -> bool:
        """True when this record may inform a prediction at ``origin``."""
        return self.known_date <= origin

    def is_retrospective_for(self, origin: date) -> bool:
        """True when the fact applied before the origin but became known after it."""
        return self.effective_date <= origin < self.known_date


@dataclass(frozen=True)
class ContractRecord:
    player: str
    club: str
    start_date: date
    end_date: date
    known_date: date  # announcement date
    club_option_years: int = 0  # guaranteed years are (end - start) minus options
    source: str = ""
    confidence: float = 1.0

    def known_at(self, origin: date) -> bool:
        return self.known_date <= origin

    def horizon_days(self, as_of: date) -> int:
        """Days of contract remaining as of a date (can be negative if expired)."""
        return (self.end_date - as_of).days


def squad_continuity(
    prev_squad: set[str], current_squad: set[str]
) -> dict[str, float]:
    """Continuity metrics between two squad snapshots.

    Returns the retained fraction (players in both), the turnover fraction, and the
    counts of arrivals and departures. Continuity is a registration-spell measure;
    minutes-weighted continuity is computed elsewhere when eligible minutes exist.
    """
    retained = prev_squad & current_squad
    arrivals = current_squad - prev_squad
    departures = prev_squad - current_squad
    denom = len(prev_squad) or 1
    return {
        "retained_fraction": len(retained) / denom,
        "turnover_fraction": len(departures) / denom,
        "arrivals": float(len(arrivals)),
        "departures": float(len(departures)),
    }
