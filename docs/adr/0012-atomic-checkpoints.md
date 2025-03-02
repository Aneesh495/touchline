# ADR 0012: Atomic checkpoint writes for recovery

## Status
Accepted.

## Context
Long jobs (acquisition, training, simulation) must survive interruption without
leaving a half-written checkpoint that a resumed run would mistake for complete.

## Decision
Write every artifact and checkpoint to a temporary file in the same directory,
fsync, and rename into place. Rename within a directory is atomic on POSIX, so a
crash leaves either the old file or nothing. A sidecar sha256 lets reads detect
corruption.

## Alternatives
- Write in place: a crash mid-write corrupts the file.
- A database: heavier than needed for file-based artifacts.

## Consequences
Resumed runs continue from the last complete checkpoint without duplicate work or
corruption. The cost is a temporary file per write, which is negligible.
