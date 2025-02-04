"""Resumable job state for acquisition, training, and simulation.

A long job records its progress as an atomically written checkpoint keyed by a
job id. On restart the job reads the checkpoint and continues from the recorded
position: downloaded files are not re-fetched, completed training epochs are not
repeated, and completed simulation draws are not recounted. The identities of the
work already done are preserved so a resumed run produces the same result as an
uninterrupted one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from touchline.registry.artifacts import atomic_write_bytes


@dataclass
class JobCheckpoint:
    job_id: str
    kind: str  # "acquisition" | "training" | "simulation"
    completed_units: int  # epochs done, draws done, files fetched
    total_units: int
    done_ids: list[str] = field(default_factory=list)  # e.g. fetched file keys
    rng_state: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return self.completed_units >= self.total_units

    @property
    def remaining(self) -> int:
        return max(0, self.total_units - self.completed_units)


@dataclass
class RecoveryStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.root / f"{job_id}.job.json"

    def save(self, cp: JobCheckpoint) -> None:
        payload = json.dumps(
            {
                "job_id": cp.job_id,
                "kind": cp.kind,
                "completed_units": cp.completed_units,
                "total_units": cp.total_units,
                "done_ids": cp.done_ids,
                "rng_state": cp.rng_state,
                "extra": cp.extra,
            },
            indent=2,
        ).encode("utf-8")
        atomic_write_bytes(self._path(cp.job_id), payload)

    def load(self, job_id: str) -> JobCheckpoint | None:
        path = self._path(job_id)
        if not path.exists():
            return None
        d = json.loads(path.read_text())
        return JobCheckpoint(
            job_id=d["job_id"],
            kind=d["kind"],
            completed_units=d["completed_units"],
            total_units=d["total_units"],
            done_ids=d.get("done_ids", []),
            rng_state=d.get("rng_state"),
            extra=d.get("extra", {}),
        )

    def resume_or_start(
        self, job_id: str, kind: str, total_units: int
    ) -> JobCheckpoint:
        existing = self.load(job_id)
        if existing is not None:
            return existing
        cp = JobCheckpoint(job_id, kind, 0, total_units)
        self.save(cp)
        return cp
