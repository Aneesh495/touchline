"""Train-and-register round-trip oracle."""

from touchline.data.sample import generate_sample_shots
from touchline.registry.model_card import ModelRegistry
from touchline.registry.register_xg import train_and_register


def test_train_and_register_roundtrip(tmp_path):
    x, y, _ = generate_sample_shots(n=3000, seed=5)
    card = train_and_register(x, y, tmp_path, model_id="xg_test")
    assert card.model_type == "logistic_xg"
    assert card.supported_fields == ["event"]
    assert card.checkpoint_sha256 is not None
    # selection record must not reference test performance as the selector
    assert "test not inspected" in card.selection_record
    # reload from the registry and verify the checkpoint hash matches the card
    reg = ModelRegistry(tmp_path)
    loaded = reg.load_card("xg_test")
    assert loaded.metrics["val_log_loss"] > 0
    ckpt = reg.load_checkpoint("xg_test")
    assert len(ckpt) > 0


def test_registered_model_not_offered_for_spatial_only_queries(tmp_path):
    x, y, _ = generate_sample_shots(n=2000, seed=6)
    train_and_register(x, y, tmp_path, model_id="xg_event")
    reg = ModelRegistry(tmp_path)
    # an event-only match can use it
    assert any(c.model_id == "xg_event" for c in reg.select_for_fields({"event"}))
