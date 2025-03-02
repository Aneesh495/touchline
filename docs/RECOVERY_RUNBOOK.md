# Recovery runbook

How to resume an interrupted acquisition, training, or simulation without losing or
duplicating work.

## Principle

Every long job writes an atomic checkpoint keyed by a job id (`registry.recovery`).
On restart, call `resume_or_start(job_id, kind, total_units)`; it returns the saved
progress if the job exists and a fresh checkpoint otherwise. Completed units are not
redone.

## Acquisition

Acquisition progress lives in the content cache (`data/raw/cache/index.json`) plus
the request budget snapshot. A resumed `acquire_many` skips keys already cached
(they do not consume budget) and continues from where it stopped. If a fetch failed,
rerun the same command; the cache serves the completed files and only the missing
ones are fetched, within the remaining budget.

Steps:
1. Inspect `data/raw/cache/index.json` to see what is already present.
2. Rerun the ingest command with the same budget; completed files are skipped.
3. If the budget was exhausted, raise `--max-requests` or run again later.

## Training

1. Load the job checkpoint for the training job id.
2. If `is_complete`, the checkpoint is final; load it from the registry.
3. Otherwise resume from `completed_units` (epochs) using the saved RNG state so the
   continuation matches an uninterrupted run.

## Simulation

1. Load the simulation job checkpoint.
2. `completed_units` is the number of draws already recorded; continue for the
   remaining draws. Completed draws are never recounted, so a resumed run produces
   the same distribution as an uninterrupted one.

## Integrity

Checkpoints are written atomically (temp file plus rename) with a sidecar sha256, so
a crash mid-write leaves either the old checkpoint or nothing, never a corrupt one.
A read that detects a checksum mismatch raises rather than returning bad bytes.
