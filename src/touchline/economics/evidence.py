"""Structured evidence import and review for manual primary-source records.

Transfer and contract facts often come from club announcements that a human reads
and records. To keep those reproducible and auditable, each manual record is
imported as an evidence item with its source URL or citation, the recorder, the
date recorded, and a review status. Nothing enters the modelling set until it is
reviewed, and the evidence trail is preserved so a later reader can check the
primary source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class ReviewStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class EvidenceItem:
    item_id: str
    kind: str  # "transfer" | "contract"
    payload: dict[str, Any]
    source_citation: str  # URL or publication reference
    recorded_by: str
    recorded_on: date
    status: ReviewStatus = ReviewStatus.PENDING
    review_note: str = ""

    def accept(self, note: str = "") -> None:
        self.status = ReviewStatus.ACCEPTED
        self.review_note = note

    def reject(self, note: str) -> None:
        self.status = ReviewStatus.REJECTED
        self.review_note = note


@dataclass
class EvidenceLedger:
    items: list[EvidenceItem] = field(default_factory=list)

    def add(self, item: EvidenceItem) -> None:
        if any(x.item_id == item.item_id for x in self.items):
            raise ValueError(f"duplicate evidence id {item.item_id!r}")
        self.items.append(item)

    def pending(self) -> list[EvidenceItem]:
        return [i for i in self.items if i.status is ReviewStatus.PENDING]

    def accepted(self) -> list[EvidenceItem]:
        return [i for i in self.items if i.status is ReviewStatus.ACCEPTED]

    def require_source(self) -> list[str]:
        """Return ids of items lacking a source citation; these cannot be accepted."""
        return [i.item_id for i in self.items if not i.source_citation.strip()]
