"""Feature registry with explicit knowledge time.

A feature is described once by a :class:`FeatureSpec`: its name, the entity grain
it applies to, and whether it is observable before a match, during a match at a
given clock, or only after the match. A concrete :class:`FeatureValue` carries the
value together with the :class:`KnowledgeTime` at which it became known.

The registry's :meth:`check_usable` answers the only question that matters for
leakage: may this feature inform a prediction whose origin is ``origin``? The
answer is yes exactly when the feature was knowable at or before the origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

from touchline.domain.clock import MatchClock


class Availability(str, Enum):
    PRE_MATCH = "pre_match"  # known before kickoff (e.g. prior Elo)
    IN_MATCH = "in_match"  # known at a specific clock during the match
    POST_MATCH = "post_match"  # known only after the match ends (labels, final table)


@dataclass(frozen=True)
class KnowledgeTime:
    """When a fact became known: a calendar date and, optionally, a match clock.

    ``match_date`` locates the fact on the season timeline. ``clock`` locates it
    within a match for in-match features. A pre-match feature has ``clock=None``
    and is knowable from the start of its date; a post-match feature is marked so
    it can never precede an in-match origin on the same date.
    """

    match_date: date | None
    clock: MatchClock | None
    availability: Availability

    def precedes_origin(self, origin: KnowledgeTime) -> bool:
        """True when a fact known at ``self`` may inform a prediction at ``origin``."""
        # Post-match facts can never inform an in-match or pre-match origin for the
        # same match, regardless of date equality.
        if self.availability is Availability.POST_MATCH and origin.availability in (
            Availability.PRE_MATCH,
            Availability.IN_MATCH,
        ):
            if self.match_date == origin.match_date:
                return False
        if self.match_date is not None and origin.match_date is not None:
            if self.match_date < origin.match_date:
                return True
            if self.match_date > origin.match_date:
                return False
            # same date: fall through to clock comparison
        if self.clock is not None and origin.clock is not None:
            return self.clock <= origin.clock
        # pre-match feature informing a same-date in-match origin is allowed
        if self.availability is Availability.PRE_MATCH:
            return True
        return self.clock is None


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    grain: str  # "match" | "team" | "player" | "shot" | "possession"
    availability: Availability
    unit: str = ""
    description: str = ""


@dataclass(frozen=True)
class FeatureValue:
    spec: FeatureSpec
    value: Any
    knowledge: KnowledgeTime


@dataclass
class FeatureRegistry:
    """Holds feature specs and enforces the knowledge-time contract on use."""

    specs: dict[str, FeatureSpec] = field(default_factory=dict)

    def register(self, spec: FeatureSpec) -> FeatureSpec:
        if spec.name in self.specs and self.specs[spec.name] != spec:
            raise ValueError(f"feature {spec.name!r} already registered differently")
        self.specs[spec.name] = spec
        return spec

    def check_usable(self, value: FeatureValue, origin: KnowledgeTime) -> bool:
        if value.spec.name not in self.specs:
            raise KeyError(f"unregistered feature {value.spec.name!r}")
        return value.knowledge.precedes_origin(origin)
