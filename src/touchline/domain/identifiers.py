"""Provider-scoped identifiers.

Every id remembers where it came from. Two ids from different providers are never
equal even if the raw value matches, because provider id spaces are independent.
Linking across providers is the job of the identity resolver (see
``touchline.ingest.identity``), which produces auditable alias records rather than
silently merging ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Provider(StrEnum):
    """Known data providers kept distinct throughout the pipeline."""

    STATSBOMB = "statsbomb"
    FOOTBALL_DATA_UK = "football_data_uk"
    FOOTBALL_DATA_ORG = "football_data_org"
    OPENFOOTBALL = "openfootball"
    CANONICAL = "canonical"  # Touchline's own resolved namespace
    MANUAL = "manual"  # human-entered evidence records


@dataclass(frozen=True)
class EntityRef:
    """A reference to an entity in a specific provider namespace."""

    provider: Provider
    kind: str  # "team" | "player" | "match" | "competition"
    value: str

    def __str__(self) -> str:
        return f"{self.provider.value}:{self.kind}:{self.value}"


@dataclass(frozen=True)
class TeamId:
    provider: Provider
    value: str

    def ref(self) -> EntityRef:
        return EntityRef(self.provider, "team", self.value)


@dataclass(frozen=True)
class PlayerId:
    provider: Provider
    value: str

    def ref(self) -> EntityRef:
        return EntityRef(self.provider, "player", self.value)


@dataclass(frozen=True)
class MatchId:
    provider: Provider
    value: str

    def ref(self) -> EntityRef:
        return EntityRef(self.provider, "match", self.value)


@dataclass(frozen=True)
class CompetitionId:
    """A competition, scoped by provider and identified by a stable code.

    The ``code`` is a Touchline-stable short code (e.g. ``EPL``, ``UCL``) so that
    the same real competition carries a consistent identity across providers, while
    ``provider`` records which feed a particular record came from.
    """

    provider: Provider
    code: str

    def ref(self) -> EntityRef:
        return EntityRef(self.provider, "competition", self.code)
