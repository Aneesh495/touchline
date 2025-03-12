"""End-to-end pipeline over acquired StatsBomb data.

This assembles the coverage matrix from acquired matches, extracts shots, builds xG
features, and fits the logistic model on real parsed shots. It operates on whatever
is already in the content cache, so it runs offline after an acquisition and never
re-fetches. It is the bridge between the real-data ingest path and the models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from touchline.coverage.matrix import CoverageMatrix
from touchline.features.shots import shot_features
from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import statsbomb_events_ref, statsbomb_matches_ref
from touchline.parse.statsbomb import parse_statsbomb_events, parse_statsbomb_match


@dataclass
class PipelineResult:
    coverage: CoverageMatrix
    n_shots: int
    features: np.ndarray
    labels: np.ndarray


def build_from_cache(
    cache_root: Path,
    competition_id: int,
    season_id: int,
    competition_code: str,
    season_name: str,
    max_matches: int | None = None,
) -> PipelineResult:
    """Build coverage and xG features from cached StatsBomb data.

    Only matches whose event files are already cached contribute event-level
    coverage and shots; matches present only at the summary level contribute
    results-level coverage. This keeps the coverage report honest about depth.
    """
    cache = ContentCache(cache_root)
    mref = statsbomb_matches_ref(competition_id, season_id)
    matches_bytes = cache.get(mref.key)
    if matches_bytes is None:
        raise FileNotFoundError(f"matches not cached: {mref.key}")
    matches = json.loads(matches_bytes.decode())
    if max_matches is not None:
        matches = matches[:max_matches]

    coverage = CoverageMatrix()
    feats: list[list[float]] = []
    labels: list[int] = []
    n_shots = 0

    for m in matches:
        summary = parse_statsbomb_match(m)
        match_id = summary["match_id"]
        eref = statsbomb_events_ref(int(match_id))
        events_bytes = cache.get(eref.key)
        has_events = events_bytes is not None
        has_tracking = False
        if has_events:
            _, shots = parse_statsbomb_events(
                events_bytes.decode(), home_team_id=summary["home_team_id"]
            )
            for s in shots:
                if not s.counts_toward_regulation:
                    continue
                row = shot_features(s)
                feats.append(row.dense_vector())
                labels.append(row.is_goal)
                n_shots += 1
                if row.has_spatial:
                    has_tracking = True
        coverage.add_match(
            competition_code,
            season_name,
            match_id,
            has_events=has_events,
            has_tracking=has_tracking,
        )

    x = np.array(feats, dtype=float) if feats else np.empty((0, 7))
    y = np.array(labels, dtype=float) if labels else np.empty((0,))
    return PipelineResult(coverage, n_shots, x, y)
