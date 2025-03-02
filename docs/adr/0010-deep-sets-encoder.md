# ADR 0010: Deep Sets for the spatial encoder

## Status
Accepted.

## Context
A 360 freeze frame is a variable-length, unordered set of players with occlusions.
The encoder must be permutation invariant and handle a variable count with a mask.

## Decision
Use a Deep Sets encoder: a shared per-player MLP followed by a masked-mean pool and
a head that combines the pool with the ball features. Masked-mean pooling is
permutation invariant by construction and ignores padded slots.

## Alternatives
- A fixed-slot MLP: not permutation invariant; sensitive to ordering.
- Attention over players: more expressive but heavier and harder to prove invariant;
  the mean pool suffices and is provably invariant, which the tests check.

## Consequences
Permutation invariance and masking are guaranteed and tested. A context-removal
ablation quantifies the encoder's contribution. The cost is that the mean pool is
less expressive than attention, acceptable for the available data scale.
