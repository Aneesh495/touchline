"""Data acquisition: budgeted, checksummed, resumable, attributed.

Acquisition is deliberately conservative. It respects a request budget, records a
content checksum for every file it writes, remembers the provider revision marker
so an unchanged file is not re-downloaded, and keeps an attribution record for
licensing. Nothing here fabricates data: if a resource is unavailable the failure
is recorded and the gate that depends on it stays blocked.
"""

from touchline.ingest.budget import BudgetExceeded, RequestBudget
from touchline.ingest.cache import CacheEntry, ContentCache
from touchline.ingest.identity import AliasEvidence, IdentityResolver

__all__ = [
    "RequestBudget",
    "BudgetExceeded",
    "ContentCache",
    "CacheEntry",
    "IdentityResolver",
    "AliasEvidence",
]
