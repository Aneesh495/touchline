"""Cross-provider identity resolution with auditable evidence.

Providers name the same real club or player differently: "Man City" versus
"Manchester City FC", a StatsBomb numeric player id versus a football-data.co.uk
free-text team name. Merging these requires evidence, not a silent guess. Every
alias link carries the two references, a method, and a confidence; ambiguous
links are flagged for review rather than applied.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from touchline.domain.identifiers import EntityRef


def normalize_name(name: str) -> str:
    """Fold case, strip accents and common club suffixes for matching.

    This is only used to propose links; the original strings are preserved on the
    evidence record so a reviewer sees exactly what was matched.
    """
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    for suffix in (" fc", " cf", " afc", " sc", " club", " ac"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    for token in ("1.", "ss", "us", "as", "rc", "ogc", "fc", "cd", "ca"):
        s = s.replace(token + " ", " ")
    return " ".join(s.split())


@dataclass(frozen=True)
class AliasEvidence:
    left: EntityRef
    right: EntityRef
    method: str  # "exact" | "normalized" | "fuzzy" | "manual"
    confidence: float
    note: str = ""

    def needs_review(self) -> bool:
        return self.confidence < 0.9


@dataclass
class IdentityResolver:
    """Resolves references to a canonical key, recording how each link was made."""

    _canonical: dict[str, str] = field(default_factory=dict)  # ref str -> canonical
    evidence: list[AliasEvidence] = field(default_factory=list)

    def link(self, ref: EntityRef, canonical_key: str, evidence: AliasEvidence) -> None:
        self._canonical[str(ref)] = canonical_key
        self.evidence.append(evidence)

    def canonical(self, ref: EntityRef) -> str | None:
        return self._canonical.get(str(ref))

    def propose(self, a: EntityRef, a_name: str, b: EntityRef, b_name: str) -> AliasEvidence:
        """Propose a link between two references by comparing their names."""
        if a_name == b_name:
            return AliasEvidence(a, b, "exact", 1.0, f"exact: {a_name!r}")
        na, nb = normalize_name(a_name), normalize_name(b_name)
        if na == nb:
            return AliasEvidence(a, b, "normalized", 0.95, f"normalized to {na!r}")
        ratio = SequenceMatcher(None, na, nb).ratio()
        return AliasEvidence(
            a, b, "fuzzy", round(ratio, 3), f"fuzzy {a_name!r} ~ {b_name!r}"
        )

    def review_queue(self) -> list[AliasEvidence]:
        return [e for e in self.evidence if e.needs_review()]
