"""Match time that respects how football is actually timed.

Football time is piecewise. Each period restarts the minute counter, the lengths
differ (45, 45, 15, 15 plus added time), and a penalty shootout is not played on
the match clock at all. Collapsing everything into one 0..90+ axis loses the
information that matters for score-state features and for separating regulation
from extra time and from shootouts.

A :class:`MatchClock` is therefore (period, second_in_period, added_second). The
``added_second`` is only non-zero during stoppage time of a period. Ordering is
defined so that events sort correctly across the whole match without pretending
the periods share a clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import total_ordering


class PeriodKind(StrEnum):
    """Kinds of period, in the order they can occur within a match."""

    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"
    EXTRA_FIRST = "extra_first"
    EXTRA_SECOND = "extra_second"
    SHOOTOUT = "shootout"

    @property
    def order(self) -> int:
        return {
            PeriodKind.FIRST_HALF: 0,
            PeriodKind.SECOND_HALF: 1,
            PeriodKind.EXTRA_FIRST: 2,
            PeriodKind.EXTRA_SECOND: 3,
            PeriodKind.SHOOTOUT: 4,
        }[self]

    @property
    def is_regulation(self) -> bool:
        return self in (PeriodKind.FIRST_HALF, PeriodKind.SECOND_HALF)

    @property
    def is_shootout(self) -> bool:
        return self is PeriodKind.SHOOTOUT

    @property
    def nominal_seconds(self) -> int:
        """Nominal length used only to place the clock on a monotone axis."""
        return {
            PeriodKind.FIRST_HALF: 45 * 60,
            PeriodKind.SECOND_HALF: 45 * 60,
            PeriodKind.EXTRA_FIRST: 15 * 60,
            PeriodKind.EXTRA_SECOND: 15 * 60,
            PeriodKind.SHOOTOUT: 0,
        }[self]


@dataclass(frozen=True)
class Period:
    """A single period with its kind and index (1-based within its kind use)."""

    kind: PeriodKind
    number: int  # provider period number, kept as given

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError(f"period number must be >= 1, got {self.number}")


@total_ordering
@dataclass(frozen=True)
class MatchClock:
    """A point in match time.

    Parameters
    ----------
    period:
        Which period this time belongs to.
    second:
        Seconds elapsed within the regular span of the period (0 .. nominal).
    added:
        Added (stoppage) seconds beyond the regular span. Zero outside stoppage
        time. Kept separate so "45:00 + 2:00" is distinguishable from an
        impossible "47:00" of a 45 minute half.
    """

    period: PeriodKind
    second: int
    added: int = 0

    def __post_init__(self) -> None:
        if self.second < 0:
            raise ValueError("second must be non-negative")
        if self.added < 0:
            raise ValueError("added must be non-negative")
        if self.period.is_shootout and (self.added != 0):
            raise ValueError("shootout kicks have no added time")

    @property
    def is_regulation(self) -> bool:
        return self.period.is_regulation

    @property
    def is_shootout(self) -> bool:
        return self.period.is_shootout

    def display(self) -> str:
        """Human string like '45+2' or '67' or 'SO'."""
        if self.period.is_shootout:
            return "SO"
        minute = self.second // 60
        if self.added > 0:
            return f"{minute}+{self.added // 60}"
        return str(minute)

    def _sort_key(self) -> tuple[int, int, int]:
        # Period order dominates; within a period regular seconds then added.
        return (self.period.order, self.second, self.added)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MatchClock):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchClock):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __hash__(self) -> int:
        return hash(self._sort_key())

    def monotone_second(self) -> int:
        """A single increasing axis across the whole match for plotting.

        This is a derived convenience only. It accumulates nominal period lengths
        so later periods sort after earlier ones; it is never treated as the real
        elapsed wall-clock time and shootouts are placed after everything.
        """
        base = 0
        for kind in PeriodKind:
            if kind.order < self.period.order:
                base += kind.nominal_seconds
        return base + self.second + self.added
