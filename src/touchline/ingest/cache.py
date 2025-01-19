"""Content-addressed cache with change detection.

Every acquired file is stored with a sha256 of its bytes and the provider's
revision marker (e.g. a StatsBomb ``match_updated`` timestamp or an HTTP ETag).
A later run can ask whether a resource changed: if the stored revision marker
matches, the download is skipped. This gives resumable, idempotent acquisition
without trusting the file's mere existence as proof of its content.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    key: str
    sha256: str
    size: int
    revision: str | None  # provider revision marker, if any
    attribution: str  # license / source note stored alongside the bytes


class ContentCache:
    """A directory-backed cache keyed by a caller-chosen key.

    The index lives in ``index.json`` next to the stored blobs. The cache never
    overwrites a blob whose checksum already matches, and it refuses to return
    bytes whose on-disk checksum disagrees with the recorded one, catching silent
    corruption rather than trusting the file.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.json"
        self._index: dict[str, dict] = {}
        if self.index_path.exists():
            self._index = json.loads(self.index_path.read_text())

    def _blob_path(self, sha: str) -> Path:
        return self.root / "blobs" / sha[:2] / sha

    def has_current(self, key: str, revision: str | None) -> bool:
        """True when the key is cached and its revision marker is unchanged."""
        entry = self._index.get(key)
        if entry is None:
            return False
        if revision is None:
            return True
        return entry.get("revision") == revision

    def get(self, key: str) -> bytes | None:
        entry = self._index.get(key)
        if entry is None:
            return None
        blob = self._blob_path(entry["sha256"])
        if not blob.exists():
            return None
        data = blob.read_bytes()
        if sha256_bytes(data) != entry["sha256"]:
            raise ValueError(f"cache corruption detected for key {key!r}")
        return data

    def put(
        self,
        key: str,
        data: bytes,
        revision: str | None,
        attribution: str,
    ) -> CacheEntry:
        sha = sha256_bytes(data)
        blob = self._blob_path(sha)
        blob.parent.mkdir(parents=True, exist_ok=True)
        if not blob.exists():
            blob.write_bytes(data)
        entry = CacheEntry(
            key=key,
            sha256=sha,
            size=len(data),
            revision=revision,
            attribution=attribution,
        )
        self._index[key] = asdict(entry)
        self._flush()
        return entry

    def _flush(self) -> None:
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._index, indent=2, sort_keys=True))
        tmp.replace(self.index_path)

    def entries(self) -> list[CacheEntry]:
        return [CacheEntry(**v) for v in self._index.values()]
