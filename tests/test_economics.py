"""Squad economics, bitemporal integrity, and evidence workflow oracles."""

from datetime import date

import pytest

from touchline.economics.evidence import (
    EvidenceItem,
    EvidenceLedger,
    ReviewStatus,
)
from touchline.economics.transfers import (
    ContractRecord,
    FeeInterval,
    TransferRecord,
    TransferType,
    squad_continuity,
)


def test_transfer_knowledge_time_blocks_future_announcement():
    t = TransferRecord(
        player="A",
        from_club="X",
        to_club="Y",
        transfer_type=TransferType.PERMANENT,
        effective_date=date(2023, 1, 10),
        known_date=date(2023, 1, 12),
        fee=FeeInterval(10e6, 12e6),
        source="club announcement",
    )
    # A forecast made on Jan 11 cannot use a move announced Jan 12.
    assert t.known_at(date(2023, 1, 11)) is False
    assert t.known_at(date(2023, 1, 13)) is True
    # It applied before the origin but was known after: retrospective.
    assert t.is_retrospective_for(date(2023, 1, 11)) is True


def test_fee_intervals_and_unknown():
    disclosed = FeeInterval(10e6, 14e6)
    assert disclosed.midpoint() == 12e6
    undisclosed = FeeInterval.undisclosed()
    assert undisclosed.disclosed is False
    assert undisclosed.midpoint() is None
    free = FeeInterval.free()
    assert free.midpoint() == 0.0


def test_contract_horizon():
    c = ContractRecord(
        player="A",
        club="Y",
        start_date=date(2022, 7, 1),
        end_date=date(2026, 6, 30),
        known_date=date(2022, 6, 20),
    )
    assert c.horizon_days(date(2025, 6, 30)) == 365
    assert c.known_at(date(2022, 6, 25)) is True


def test_squad_continuity():
    prev = {"a", "b", "c", "d"}
    cur = {"b", "c", "d", "e"}
    m = squad_continuity(prev, cur)
    assert m["retained_fraction"] == 0.75
    assert m["turnover_fraction"] == 0.25
    assert m["arrivals"] == 1.0
    assert m["departures"] == 1.0


def test_evidence_workflow_requires_source_and_review():
    ledger = EvidenceLedger()
    item = EvidenceItem(
        item_id="e1",
        kind="contract",
        payload={"player": "A", "club": "Y"},
        source_citation="https://club.example/announcement",
        recorded_by="analyst",
        recorded_on=date(2023, 1, 1),
    )
    ledger.add(item)
    assert ledger.pending() == [item]
    assert ledger.require_source() == []  # has a source
    item.accept("verified against the club site")
    assert ledger.accepted() == [item]
    assert item.status is ReviewStatus.ACCEPTED


def test_evidence_without_source_flagged():
    ledger = EvidenceLedger()
    item = EvidenceItem(
        item_id="e2",
        kind="transfer",
        payload={},
        source_citation="   ",
        recorded_by="analyst",
        recorded_on=date(2023, 1, 1),
    )
    ledger.add(item)
    assert ledger.require_source() == ["e2"]


def test_evidence_duplicate_id_rejected():
    ledger = EvidenceLedger()
    item = EvidenceItem("e3", "transfer", {}, "src", "a", date(2023, 1, 1))
    ledger.add(item)
    with pytest.raises(ValueError):
        ledger.add(EvidenceItem("e3", "transfer", {}, "src", "a", date(2023, 1, 1)))
