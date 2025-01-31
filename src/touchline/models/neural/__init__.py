"""Neural models built on PyTorch.

These modules import torch lazily through :func:`require_torch` so the rest of the
package installs and runs on hosts without a torch wheel; calling a neural model
without torch raises a clear error rather than failing at import time.

Models:

* :mod:`spatial_xg` a small MLP xG model on the always-available shot features.
* :mod:`set_encoder` a permutation-invariant masked set encoder over the players
  visible in a 360 freeze frame, with explicit missing-player masks.
* :mod:`sequence_encoder` a causal possession-sequence encoder with padded-batch
  correctness and causal masking.
"""

from __future__ import annotations


def require_torch():
    """Import and return the torch module, with a helpful error if missing."""
    try:
        import torch

        return torch
    except ImportError as exc:  # pragma: no cover - exercised only without torch
        raise ImportError(
            "This model needs PyTorch. Install the optional extra: "
            "uv pip install -e '.[learn]'"
        ) from exc
