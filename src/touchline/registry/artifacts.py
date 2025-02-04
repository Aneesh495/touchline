"""Atomic, checksummed artifact storage.

Every artifact is written through :func:`atomic_write_bytes`, which writes to a
temporary file in the same directory and renames it into place. Rename within a
directory is atomic on POSIX filesystems, so a crash mid-write leaves either the
old artifact or nothing, never a corrupt partial file. Each stored artifact has a
sidecar ``.sha256`` so integrity can be checked on read.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


class AtomicWriteError(RuntimeError):
    pass


def atomic_write_bytes(path: Path, data: bytes) -> str:
    """Write ``data`` to ``path`` atomically and return its sha256.

    A temporary file in the same directory is written, flushed, fsync'd, and then
    renamed over the target. The returned checksum lets the caller verify the
    bytes landed as intended.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(data).hexdigest()
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except OSError as exc:  # pragma: no cover - filesystem failure path
        if tmp.exists():
            tmp.unlink()
        raise AtomicWriteError(str(exc)) from exc
    (path.parent / (path.name + ".sha256")).write_text(sha)
    return sha


@dataclass
class ArtifactStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, name: str, data: bytes) -> str:
        return atomic_write_bytes(self.root / name, data)

    def get(self, name: str) -> bytes:
        path = self.root / name
        data = path.read_bytes()
        expected_path = self.root / (name + ".sha256")
        if expected_path.exists():
            expected = expected_path.read_text().strip()
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected:
                raise AtomicWriteError(
                    f"checksum mismatch for {name}: {actual} != {expected}"
                )
        return data

    def exists(self, name: str) -> bool:
        return (self.root / name).exists()
