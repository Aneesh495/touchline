"""Registry, model card, and recovery oracles."""

import pytest

from touchline.registry.artifacts import ArtifactStore, AtomicWriteError, atomic_write_bytes
from touchline.registry.model_card import ModelCard, ModelRegistry
from touchline.registry.recovery import JobCheckpoint, RecoveryStore


def test_atomic_write_and_checksum(tmp_path):
    p = tmp_path / "a" / "b.bin"
    sha = atomic_write_bytes(p, b"payload")
    assert p.read_bytes() == b"payload"
    assert (p.parent / (p.name + ".sha256")).read_text() == sha
    # no leftover temp files
    assert not any(x.name.startswith("b.bin.tmp") for x in p.parent.iterdir())


def test_artifact_store_detects_corruption(tmp_path):
    store = ArtifactStore(tmp_path)
    store.put("m.ckpt", b"model-bytes")
    (tmp_path / "m.ckpt").write_bytes(b"tampered")
    with pytest.raises(AtomicWriteError):
        store.get("m.ckpt")


def test_model_card_roundtrip_and_checkpoint_hash(tmp_path):
    reg = ModelRegistry(tmp_path)
    card = ModelCard(
        model_id="xg_logistic_v1",
        model_type="logistic_xg",
        dataset_version="sample-v1",
        feature_contract=["distance_m", "angle_rad"],
        supported_fields=["event"],
        calibration="platt",
        selection_record="lowest validation log loss among event-only models",
        metrics={"val_log_loss": 0.41},
        seeds=[0, 1, 2],
    )
    reg.register(card, checkpoint=b"weights")
    loaded = reg.load_card("xg_logistic_v1")
    assert loaded.model_type == "logistic_xg"
    assert reg.load_checkpoint("xg_logistic_v1") == b"weights"


def test_feature_gated_model_selection(tmp_path):
    reg = ModelRegistry(tmp_path)
    reg.register(
        ModelCard("event_xg", "logistic_xg", "v1", [], ["event"], None, "sel")
    )
    reg.register(
        ModelCard("spatial_xg", "set_encoder", "v1", [], ["event", "spatial"], None, "sel")
    )
    # Event-only match: spatial model must not be offered.
    event_only = reg.select_for_fields({"event"})
    assert {c.model_id for c in event_only} == {"event_xg"}
    # Spatial match: both are eligible.
    with_spatial = reg.select_for_fields({"event", "spatial"})
    assert {c.model_id for c in with_spatial} == {"event_xg", "spatial_xg"}


def test_recovery_resume_does_not_restart(tmp_path):
    store = RecoveryStore(tmp_path)
    cp = store.resume_or_start("job1", "training", total_units=10)
    cp.completed_units = 4
    cp.done_ids = ["f1", "f2", "f3", "f4"]
    store.save(cp)
    # Simulate a restart: resume reads existing progress.
    resumed = store.resume_or_start("job1", "training", total_units=10)
    assert resumed.completed_units == 4
    assert resumed.remaining == 6
    assert resumed.done_ids == ["f1", "f2", "f3", "f4"]


def test_recovery_completion_flag():
    cp = JobCheckpoint("j", "simulation", completed_units=100, total_units=100)
    assert cp.is_complete
    assert cp.remaining == 0
