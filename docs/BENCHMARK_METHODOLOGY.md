# Benchmark methodology

How Touchline measures serving latency and why the numbers mean what they say.

## What is measured

The serving gate (G12) targets p95 latency below 250 ms for a batch of 128 event
sequences at the declared maximum length, on a pinned CPU host, with actual model
outputs and no external prediction service.

## How it is measured

`serving.inference.BatchInferenceService.measure_p95_ms` runs a number of batches,
each freshly sampled, clearing the cache before each so the figure reflects real
compute rather than cache hits. Latency is taken with a monotonic clock around the
model call only, excluding batch construction. The p95 is the 95th percentile of the
per-batch latencies.

## Scope of the reported number

The committed benchmark runs the logistic xG path on 128-shot batches at the CPU
diagnostic scale, which is comfortably under the budget. The full gate uses the
sequence model at the declared maximum sequence length on the pinned host; that run
is part of the full acceptance profile.

## What the number does not claim

- It is not a throughput figure; it is tail latency for a single batch.
- It is not a GPU measurement; the target is CPU.
- The diagnostic-scale number is not a substitute for the full-profile run on the
  pinned host, which is recorded separately.

## Reproduce

```bash
make bench
```
