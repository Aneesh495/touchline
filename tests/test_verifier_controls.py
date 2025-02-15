"""Semantic negative controls for the verifier (gate G14).

Each control makes a structurally valid copy of a real evidence bundle, alters one
meaningful quantity, and invokes the verifier as a subprocess. The verifier must
reject for a semantic reason, not merely because a hash changed. We also check the
clean bundle passes and that a missing artifact is caught.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from touchline.acceptance.run import run_acceptance
from touchline.verify.verifier import verify_evidence


@pytest.fixture(scope="module")
def clean_bundle(tmp_path_factory):
    root = tmp_path_factory.mktemp("evidence")
    rc = run_acceptance("clean", profile="cpu", root=str(root))
    assert rc == 0
    return root / "clean"


def _copy(bundle: Path, dest: Path) -> Path:
    shutil.copytree(bundle, dest)
    return dest


def _run_verifier_subprocess(path: Path) -> int:
    """Invoke the real verifier as a separate process and return its exit code."""
    code = (
        "import sys; from touchline.verify.verifier import verify_evidence; "
        f"sys.exit(0 if verify_evidence({str(path)!r}) else 1)"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    return proc.returncode


def test_clean_bundle_passes(clean_bundle):
    assert verify_evidence(str(clean_bundle)) is True
    assert _run_verifier_subprocess(clean_bundle) == 0


def test_control_future_feature_leakage(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "leak")
    recs = json.loads((dest / "feature_records.json").read_text())
    # Make a pre-match feature become known after its origin: leakage.
    recs[0]["availability"] = "post_match"
    recs[0]["knowledge_date"] = recs[0]["origin_date"]
    (dest / "feature_records.json").write_text(json.dumps(recs))
    assert _run_verifier_subprocess(dest) == 1


def test_control_flipped_pitch_direction(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "flip")
    shots = json.loads((dest / "shot_records.json").read_text())
    for s in shots:
        s["canonical_x"] = 1.0 - s["canonical_x"]  # flip the pitch
    (dest / "shot_records.json").write_text(json.dumps(shots))
    assert _run_verifier_subprocess(dest) == 1


def test_control_altered_goal_labels(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "labels")
    shots = json.loads((dest / "shot_records.json").read_text())
    # Flip a non-goal to a goal without changing the recorded score: inconsistency.
    for s in shots:
        if s["is_goal"] == 0:
            s["is_goal"] = 1
            break
    (dest / "shot_records.json").write_text(json.dumps(shots))
    assert _run_verifier_subprocess(dest) == 1


def test_control_impossible_qualification(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "qual")
    sims = json.loads((dest / "sim_records.json").read_text())
    # Mark a bottom team as qualified from an impossible position.
    sims[0]["position"] = sims[0]["cutoff"] + 3
    sims[0]["qualified"] = True
    (dest / "sim_records.json").write_text(json.dumps(sims))
    assert _run_verifier_subprocess(dest) == 1


def test_control_altered_replay_metric(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "metric")
    claimed = json.loads((dest / "xg_claimed.json").read_text())
    claimed["xg_log_loss"] = claimed["xg_log_loss"] * 0.5  # claim a better score
    (dest / "xg_claimed.json").write_text(json.dumps(claimed))
    # Replay from the saved weights reproduces the true metric and rejects the claim.
    assert _run_verifier_subprocess(dest) == 1


def test_missing_artifact_rejected(clean_bundle, tmp_path):
    dest = _copy(clean_bundle, tmp_path / "missing")
    (dest / "MANIFEST.json").unlink()
    assert _run_verifier_subprocess(dest) == 1
