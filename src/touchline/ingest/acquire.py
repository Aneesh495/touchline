"""Budgeted HTTP acquisition that ties the budget and cache together.

This is the resumable acquisition path (T01). It fetches a URL only when the cache
does not already hold a current copy, charges each real request against the
budget, stores the bytes with their checksum and an attribution note, and records
the provider revision marker so a later run skips unchanged resources. Network
failures are surfaced, not swallowed: a failed fetch leaves the cache unchanged
and the caller decides whether to retry within budget.

The actual HTTP call is injected so tests exercise the full logic without the
network, and so the same code serves real downloads in production.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from touchline.ingest.budget import RequestBudget
from touchline.ingest.cache import ContentCache

# A fetcher returns (bytes, revision_marker) or raises on failure.
Fetcher = Callable[[str], tuple[bytes, str | None]]


@dataclass
class AcquisitionResult:
    key: str
    from_cache: bool
    sha256: str | None
    bytes_len: int


class Acquirer:
    def __init__(
        self,
        cache: ContentCache,
        budget: RequestBudget,
        fetcher: Fetcher,
        attribution: str = "",
    ):
        self.cache = cache
        self.budget = budget
        self.fetcher = fetcher
        self.attribution = attribution

    def acquire(
        self, key: str, url: str, expected_revision: str | None = None
    ) -> AcquisitionResult:
        """Return the resource, fetching only if the cache copy is not current."""
        if self.cache.has_current(key, expected_revision):
            data = self.cache.get(key)
            if data is not None:
                return AcquisitionResult(key, True, None, len(data))
        self.budget.acquire()
        data, revision = self.fetcher(url)
        entry = self.cache.put(key, data, revision, self.attribution)
        return AcquisitionResult(key, False, entry.sha256, len(data))

    def acquire_many(
        self, items: list[tuple[str, str]]
    ) -> list[AcquisitionResult]:
        """Acquire a list of (key, url) pairs, stopping if the budget is exhausted.

        Already-cached items do not consume budget, so a resumed run completes the
        remaining downloads without re-fetching finished ones.
        """
        results: list[AcquisitionResult] = []
        for key, url in items:
            try:
                results.append(self.acquire(key, url))
            except Exception:
                # Preserve progress; the caller can inspect how far we got.
                break
        return results
