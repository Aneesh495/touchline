"""Model cards: the provenance record attached to every registered model.

A model card captures what a model is, how it was trained, and what it may be
used for. The ``supported_fields`` list is a hard contract: serving must refuse
inputs that require a field the model was not trained to consume (for example,
asking an event-only model for off-ball valuation). The ``selection_record``
documents why this model was chosen without reference to test performance, so the
selection rule is auditable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from touchline.registry.artifacts import ArtifactStore


@dataclass
class ModelCard:
    model_id: str
    model_type: str  # e.g. "logistic_xg", "dixon_coles", "sequence_encoder"
    dataset_version: str
    feature_contract: list[str]
    supported_fields: list[str]  # e.g. ["event"] or ["event", "spatial"]
    calibration: str | None  # name of calibrator or None
    selection_record: str  # how this model was selected (not on test perf)
    metrics: dict[str, float] = field(default_factory=dict)
    seeds: list[int] = field(default_factory=list)
    checkpoint_sha256: str | None = None
    created_at: str | None = None

    def requires_spatial(self) -> bool:
        return "spatial" in self.supported_fields

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> ModelCard:
        return cls(**json.loads(text))


@dataclass
class ModelRegistry:
    """A directory of model cards plus their checkpoint artifacts."""

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.store = ArtifactStore(self.root / "checkpoints")
        self.cards_dir = self.root / "cards"
        self.cards_dir.mkdir(parents=True, exist_ok=True)

    def register(self, card: ModelCard, checkpoint: bytes | None = None) -> ModelCard:
        if checkpoint is not None:
            sha = self.store.put(f"{card.model_id}.ckpt", checkpoint)
            card.checkpoint_sha256 = sha
        (self.cards_dir / f"{card.model_id}.json").write_text(card.to_json())
        return card

    def load_card(self, model_id: str) -> ModelCard:
        return ModelCard.from_json((self.cards_dir / f"{model_id}.json").read_text())

    def load_checkpoint(self, model_id: str) -> bytes:
        card = self.load_card(model_id)
        data = self.store.get(f"{model_id}.ckpt")
        import hashlib

        if card.checkpoint_sha256 and hashlib.sha256(data).hexdigest() != card.checkpoint_sha256:
            raise ValueError(f"checkpoint for {model_id} does not match card hash")
        return data

    def list_models(self) -> list[str]:
        return sorted(p.stem for p in self.cards_dir.glob("*.json"))

    def select_for_fields(self, available_fields: set[str]) -> list[ModelCard]:
        """Return cards whose supported fields are all available.

        This is how feature-gated model selection (T13) is enforced: a model that
        requires spatial context is not offered for an event-only match.
        """
        cards = [self.load_card(m) for m in self.list_models()]
        return [c for c in cards if set(c.supported_fields) <= available_fields]

    def summary(self) -> dict[str, Any]:
        return {m: asdict(self.load_card(m)) for m in self.list_models()}
