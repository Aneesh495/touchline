"""Ingest layer oracles: budget, cache, identity."""

import pytest

from touchline.domain.identifiers import EntityRef, Provider
from touchline.ingest.budget import BudgetExceeded, RequestBudget
from touchline.ingest.cache import ContentCache
from touchline.ingest.identity import IdentityResolver, normalize_name


def test_budget_caps_requests():
    b = RequestBudget(max_requests=2)
    b.acquire(sleeper=lambda _: None, clock=lambda: 0.0)
    b.acquire(sleeper=lambda _: None, clock=lambda: 0.0)
    with pytest.raises(BudgetExceeded):
        b.acquire(sleeper=lambda _: None, clock=lambda: 0.0)
    assert b.used == 2 and b.remaining == 0


def test_budget_resume_roundtrip():
    b = RequestBudget(max_requests=5)
    b.acquire(sleeper=lambda _: None, clock=lambda: 0.0)
    restored = RequestBudget.restore(b.snapshot())
    assert restored.used == 1 and restored.remaining == 4


def test_cache_change_detection_and_integrity(tmp_path):
    cache = ContentCache(tmp_path)
    cache.put("k1", b"hello", revision="v1", attribution="test")
    assert cache.has_current("k1", "v1") is True
    assert cache.has_current("k1", "v2") is False
    assert cache.get("k1") == b"hello"
    # A reopened cache sees the persisted entry.
    reopened = ContentCache(tmp_path)
    assert reopened.get("k1") == b"hello"


def test_cache_detects_corruption(tmp_path):
    cache = ContentCache(tmp_path)
    entry = cache.put("k", b"payload", revision=None, attribution="t")
    blob = cache.root / "blobs" / entry.sha256[:2] / entry.sha256
    blob.write_bytes(b"tampered")
    with pytest.raises(ValueError):
        ContentCache(tmp_path).get("k")


def test_name_normalisation():
    assert normalize_name("Manchester City FC") == normalize_name("Manchester City")
    assert normalize_name("Atlético Madrid") == normalize_name("Atletico Madrid")


def test_identity_proposal_confidence():
    r = IdentityResolver()
    a = EntityRef(Provider.STATSBOMB, "team", "Barcelona")
    b = EntityRef(Provider.FOOTBALL_DATA_UK, "team", "Barcelona")
    ev = r.propose(a, "Barcelona", b, "Barcelona")
    assert ev.method == "exact" and ev.confidence == 1.0
    ev2 = r.propose(a, "Man City", b, "Manchester City FC")
    assert ev2.confidence < 1.0
