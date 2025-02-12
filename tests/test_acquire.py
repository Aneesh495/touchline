"""Acquisition oracles using an injected fetcher (no network)."""

from touchline.ingest.acquire import Acquirer
from touchline.ingest.budget import RequestBudget
from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import season_code, statsbomb_events_ref


def make_acquirer(tmp_path, calls, max_requests=10, revisions=None):
    cache = ContentCache(tmp_path / "cache")
    budget = RequestBudget(max_requests=max_requests)
    revisions = revisions or {}

    def fetch(url):
        calls.append(url)
        return (f"body-for-{url}".encode(), revisions.get(url))

    return Acquirer(cache, budget, fetch, attribution="test"), budget


def test_acquire_fetches_then_caches(tmp_path):
    calls = []
    acq, budget = make_acquirer(tmp_path, calls)
    r1 = acq.acquire("k", "http://x/1")
    assert r1.from_cache is False
    assert budget.used == 1
    # Second acquire of the same key with no revision requirement hits the cache.
    r2 = acq.acquire("k", "http://x/1")
    assert r2.from_cache is True
    assert budget.used == 1  # no extra request
    assert len(calls) == 1


def test_revision_change_triggers_refetch(tmp_path):
    calls = []
    acq, budget = make_acquirer(
        tmp_path, calls, revisions={"http://x/1": "v1"}
    )
    acq.acquire("k", "http://x/1", expected_revision="v1")
    # Same revision: cached.
    acq.acquire("k", "http://x/1", expected_revision="v1")
    assert budget.used == 1
    # New revision: refetch.
    acq.acquire("k", "http://x/1", expected_revision="v2")
    assert budget.used == 2


def test_acquire_many_resumes_without_refetching(tmp_path):
    calls = []
    acq, budget = make_acquirer(tmp_path, calls, max_requests=10)
    items = [("k1", "u1"), ("k2", "u2"), ("k3", "u3")]
    acq.acquire_many(items)
    assert budget.used == 3
    # A second pass (simulating resume) fetches nothing new.
    acq.acquire_many(items)
    assert budget.used == 3


def test_acquire_many_stops_at_budget(tmp_path):
    calls = []
    acq, budget = make_acquirer(tmp_path, calls, max_requests=2)
    items = [("k1", "u1"), ("k2", "u2"), ("k3", "u3")]
    results = acq.acquire_many(items)
    # Budget of 2 allows two fetches; the third stops the loop.
    assert len(results) == 2
    assert budget.used == 2


def test_source_refs_build_expected_paths():
    assert season_code(2022) == "2223"
    ref = statsbomb_events_ref(3773386)
    assert ref.key == "statsbomb/events/3773386.json"
    assert ref.url.endswith("/events/3773386.json")
