# Serving and verification: bounded inference and independent replay

## Serving

Inference is served in bounded batches from local models only, never an external
prediction service. The service caps batch size and sequence length (rejecting
over-large requests rather than silently truncating), caches repeated inputs in a
bounded LRU, and measures p95 latency over fresh batches that bypass the cache
(`serving.inference`). On CPU the logistic xG path serves 128-shot batches well
under the 250 ms budget, which is the target of gate G12.

## Verification

The verifier is implemented separately from the acceptance runner that produces
results. It recomputes the semantic checks from raw records (no future-feature
leakage, shots in the attacking half, goal labels consistent with the score, no
impossible qualification) and replays the saved xG weights with its own forward
pass to reproduce the claimed metric, rejecting any mismatch (`verify.verifier`).
It never trusts a stored pass flag and never retrains.

## Negative controls

Four semantic negative controls corrupt a copy of a real evidence bundle (future
leakage, flipped pitch, altered goal labels, impossible qualification) and invoke
the verifier as a subprocess; all are rejected for a semantic reason. A tampered
replay metric and a missing artifact are also rejected. These are gate G14.

## Conclusion

The serving path is bounded and local; the verifier is independent and recomputes
rather than trusts. Together they make the reported results checkable by someone who
did not produce them.
