# Walkthrough: an error and recovery path

This traces what happens when acquisition is interrupted and resumed, and when a
stored artifact is corrupt.

## Interrupted acquisition

1. `ingest.acquire.Acquirer.acquire_many` (`ingest/acquire.py`) fetches a list of
   (key, url) pairs. Each successful fetch stores bytes with a checksum in the
   content cache and charges the request budget.

2. Suppose the process is killed after two of three fetches. The cache holds the
   two completed files; the budget snapshot records two used.

3. On restart, `acquire_many` is called with the same list. For each key,
   `ContentCache.has_current` (`ingest/cache.py`) reports the cached files as
   current, so they are returned from cache without a network call or budget charge.
   Only the third file is fetched. The resumed run reaches the same end state as an
   uninterrupted one.

## Corrupt artifact

1. A checkpoint is written atomically by `registry.artifacts.atomic_write_bytes`
   (temp file plus rename, sidecar sha256).

2. If the blob is later tampered with, `ArtifactStore.get` recomputes the sha256 and
   finds it does not match the sidecar, raising `AtomicWriteError` rather than
   returning the bad bytes. The same guard protects the content cache
   (`ContentCache.get`).

3. The recovery store (`registry.recovery`) likewise writes job checkpoints
   atomically, so a crash mid-write leaves the old checkpoint or nothing, never a
   half-written one that a resumed run would misread.

Tests: `tests/test_acquire.py` (resume without refetch), `tests/test_registry.py`
(corruption detection, resume), diagram `docs/diagrams/svg/11-failure-recovery.svg`.
