# Walkthrough: a shot becomes an xG prediction

This traces one shot from raw provider bytes to a served probability, with source
pointers.

1. **Parse.** `parse.statsbomb.parse_statsbomb_events` reads the event JSON. For a
   `type.name == "Shot"` it reads `location`, maps it through `SB_PITCH.to_canonical`
   (`parse/statsbomb.py`) into the canonical attacking frame, sets `is_penalty` from
   `shot.type`, `is_shootout` from the period, and `is_goal` from `shot.outcome`,
   producing a `domain.events.Shot`.

2. **Features.** `features.shots.shot_features` (`features/shots.py`) turns the shot
   into a `ShotFeatureRow`: distance via `Point.distance_to_goal_m`, angle via
   `Point.shot_angle_rad` (`domain/geometry.py`), plus body-part and situation
   flags. If the shot carries a `freeze_frame`, defender count and keeper distance
   are added; otherwise the spatial fields are `None`, so an event-only shot never
   gets fabricated spatial features.

3. **Model.** `models.xg_logistic.LogisticXG.predict_proba` (`models/xg_logistic.py`)
   standardises the row with training-time statistics and applies the logistic map.
   The neural variant `models.neural.spatial_xg.SpatialXG` is used when selected.

4. **Serve.** `serving.inference.BatchInferenceService.predict_shots`
   (`serving/inference.py`) batches the request, serves cached rows from its LRU,
   runs the model on the rest, and records the latency.

Diagram: `docs/diagrams/svg/12-shot-to-xg-path.svg`.
